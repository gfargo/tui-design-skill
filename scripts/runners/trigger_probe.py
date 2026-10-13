#!/usr/bin/env python3
"""Measure implicit activation of the tui-design skill on Claude Code or Codex.

Every trial sends one trigger-eval query, unchanged, to a host that has only
this repository's copy of the skill installed, and records whether the model
chose to load it. The prompt never names the skill.

  claude  `claude -p` in an empty directory with `--plugin-dir plugins/tui-design`
          and `--setting-sources project`, so the plugin skill
          (tui-design:tui-design) competes only with Claude Code's bundled
          skills. Triggered = a Skill tool call for tui-design:tui-design.
  codex   `codex exec` from an empty subdirectory of a scratch git repository
          whose .agents/skills/tui-design holds a copy of the skill. Every
          user-installed skill is disabled through skills.config, web search
          is off, and the sandbox is read-only. Triggered = a command that
          reads tui-design/SKILL.md.

Writes manifest.json (host, model, versions, hashes, git state), results.jsonl
(one raw outcome per trial, including the tool calls seen), and summary.json
(rates per query and per category) into --output.

Usage:
  CLAUDE_BIN=... python3 scripts/runners/trigger_probe.py --host claude \\
    --model claude-opus-5-5 --runner-version "Claude Code 2.1.295" \\
    --eval-set evals/v180-trigger-evals.json --repeat 3 --jobs 3 --output DIR
  CODEX_BIN=... python3 scripts/runners/trigger_probe.py --host codex \\
    --model gpt-6.1-sol --effort low --runner-version "codex-cli 0.160.0" \\
    --eval-set evals/v180-trigger-evals.json --repeat 3 --jobs 2 --output DIR
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from eval_harness import git_metadata, host_metadata, sha256_bytes, sha256_file, sha256_tree, utc_now  # noqa: E402

PLUGIN_DIR = REPO_ROOT / "plugins/tui-design"
SKILL_DIR = PLUGIN_DIR / "skills/tui-design"
CLAUDE_SKILL = "tui-design:tui-design"
CLAUDE_MAX_TURNS = "3"


def skill_description() -> str:
    match = re.search(r"^description:\s*(.+)$", (SKILL_DIR / "SKILL.md").read_text(), flags=re.MULTILINE)
    if not match:
        raise SystemExit("SKILL.md has no description")
    return match.group(1).strip()


def summarize_input(value) -> str:
    return json.dumps(value, ensure_ascii=False)[:160]


def run_claude(args, query):
    command = [
        os.environ.get("CLAUDE_BIN", "claude"), "-p", "--model", args.model,
        "--setting-sources", "project", "--plugin-dir", str(PLUGIN_DIR),
        "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--no-session-persistence",
        "--max-turns", CLAUDE_MAX_TURNS, "--output-format", "stream-json", "--verbose",
    ]
    if args.effort:
        command += ["--effort", args.effort]
    with tempfile.TemporaryDirectory(prefix="tui-design-trigger-") as workdir:
        completed = subprocess.run(command + [query], cwd=workdir, capture_output=True, text=True, timeout=args.timeout)
    calls, skills, loaded = [], [], None
    for line in completed.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            loaded = CLAUDE_SKILL in (event.get("skills") or [])
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    calls.append({"name": block.get("name"), "input": summarize_input(block.get("input"))})
                    if block.get("name") == "Skill":
                        skills.append((block.get("input") or {}).get("skill"))
    # A run that stops at --max-turns exits nonzero but is still a valid observation;
    # it is valid when the init event shows the plugin skill was available.
    return {
        "valid": loaded is True,
        "triggered": CLAUDE_SKILL in skills,
        "skill_loaded": loaded,
        "skills_invoked": skills,
        "tool_calls": calls[:10],
        "exit_code": completed.returncode,
    }


def codex_disabled_skills():
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    found = set()
    for root in (Path.home() / ".agents/skills", codex_home / "skills"):
        if root.is_dir():
            for skill in root.iterdir():
                if (skill / "SKILL.md").is_file():
                    found.add(str((skill / "SKILL.md").resolve()))
    entries = ",".join('{path="%s", enabled=false}' % path.replace("\\", "\\\\").replace('"', '\\"') for path in sorted(found))
    return f"skills.config=[{entries}]"


def run_codex(args, query):
    with tempfile.TemporaryDirectory(prefix="tui-design-trigger-") as scratch:
        root = Path(scratch)
        shutil.copytree(SKILL_DIR, root / ".agents/skills/tui-design")
        (root / "work").mkdir()
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        command = [
            os.environ.get("CODEX_BIN", "codex"), "exec", "-m", args.model,
            "-c", codex_disabled_skills(), "-c", 'web_search="disabled"',
            "--ignore-user-config", "--skip-git-repo-check", "--ephemeral", "-s", "read-only",
            "-C", str(root / "work"), "--color", "never", "--json", "-",
        ]
        if args.effort:
            command[4:4] = ["-c", f'model_reasoning_effort="{args.effort}"']
        completed = subprocess.run(command, input=query, capture_output=True, text=True, timeout=args.timeout)
    commands = []
    for line in completed.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        item = event.get("item") or {}
        if event.get("type") == "item.completed" and item.get("type") == "command_execution":
            commands.append(item.get("command", ""))
    reads = [c for c in commands if "tui-design/SKILL.md" in c]
    limit_hit = "usage limit" in completed.stderr or "usage limit" in completed.stdout
    return {
        "valid": completed.returncode == 0 and not limit_hit,
        "triggered": bool(reads),
        "skill_reads": [c[:200] for c in reads],
        "tool_calls": [{"name": "command", "input": c[:160]} for c in commands[:10]],
        "exit_code": completed.returncode,
        "usage_limit": limit_hit,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", required=True, choices=["claude", "codex"])
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort")
    parser.add_argument("--runner-version", required=True)
    parser.add_argument("--eval-set", required=True, type=Path)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--ids", help="comma-separated query ids to run (default: all)")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    eval_set = json.loads(args.eval_set.read_text())
    queries = eval_set["queries"]
    if args.ids:
        wanted = set(args.ids.split(","))
        queries = [q for q in queries if q["id"] in wanted]
    args.output.mkdir(parents=True, exist_ok=False)
    description = skill_description()
    manifest = {
        "artifact_type": "tui-design-trigger-calibration",
        "created_at": utc_now(),
        "host": args.host,
        "model": args.model,
        "reasoning_effort": args.effort,
        "runner_version": args.runner_version,
        "invocation": "claude -p --setting-sources project --plugin-dir plugins/tui-design"
        if args.host == "claude"
        else "codex exec with only a project-scoped copy of the skill enabled",
        "trigger_rule": f"Skill tool call for {CLAUDE_SKILL}" if args.host == "claude" else "a command that reads tui-design/SKILL.md",
        "eval_set": args.eval_set.as_posix(),
        "eval_set_sha256": sha256_file(args.eval_set),
        "skill_description": description,
        "skill_description_sha256": sha256_bytes(description.encode()),
        "skill_sha256": sha256_tree(SKILL_DIR),
        "repetitions": args.repeat,
        "git": git_metadata(),
        "host_metadata": host_metadata(),
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    runner = run_claude if args.host == "claude" else run_codex
    trials = [(q, rep) for rep in range(1, args.repeat + 1) for q in queries]

    def trial(item):
        query, rep = item
        start = time.monotonic()
        try:
            outcome = runner(args, query["query"])
        except subprocess.TimeoutExpired:
            outcome = {"valid": False, "triggered": None, "error": "timeout"}
        record = {
            "id": query["id"], "category": query["category"], "should_trigger": query["should_trigger"],
            "repetition": rep, "duration_seconds": round(time.monotonic() - start, 1), **outcome,
        }
        print(f"{query['id']} r{rep}: triggered={record['triggered']}", file=sys.stderr, flush=True)
        return record

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        records = list(pool.map(trial, trials))
    records.sort(key=lambda r: (r["id"], r["repetition"]))
    with (args.output / "results.jsonl").open("w") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    by_query = defaultdict(list)
    for record in records:
        by_query[record["id"]].append(record)
    per_query = []
    per_category = defaultdict(lambda: {"triggered": 0, "trials": 0, "invalid": 0})
    for query in queries:
        rows = by_query[query["id"]]
        valid = [r for r in rows if r["valid"]]
        fired = sum(1 for r in valid if r["triggered"])
        per_query.append({"id": query["id"], "category": query["category"], "should_trigger": query["should_trigger"],
                          "triggered": fired, "trials": len(valid), "invalid": len(rows) - len(valid)})
        bucket = per_category[query["category"]]
        bucket["triggered"] += fired
        bucket["trials"] += len(valid)
        bucket["invalid"] += len(rows) - len(valid)
    summary = {"completed_at": utc_now(), "per_category": per_category, "per_query": per_query}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    for category, bucket in per_category.items():
        print(f"{category}: {bucket['triggered']}/{bucket['trials']} triggered ({bucket['invalid']} invalid)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
