#!/usr/bin/env python3
"""Eval-harness runner for the Codex CLI: prompt on stdin, final answer on stdout.

Runs `codex exec` from an empty temporary directory, read-only and ephemeral,
without the user's config.toml, with web search disabled (Claude Code runs get
no web tools either), and with every user-installed skill disabled
through `skills.config` (skills under ~/.agents/skills and $CODEX_HOME/skills),
so the baseline condition cannot pick up an installed copy of this skill.
Codex's bundled system skills stay available in both conditions. A with-skill
prompt names the skill directory explicitly, and the read-only sandbox can read it.

Usage (from scripts/eval_harness.py run ... --):
  python3 scripts/runners/codex_runner.py --model gpt-6.1-sol --effort low
Set CODEX_BIN to choose the Codex binary (default: `codex` on PATH).
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def user_skill_files() -> list:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    roots = [Path.home() / ".agents/skills", codex_home / "skills"]
    found = []
    for root in roots:
        if not root.is_dir():
            continue
        for skill in sorted(root.iterdir()):
            skill_file = skill / "SKILL.md"
            if skill_file.is_file():
                found.append(str(skill_file.resolve()))
    return sorted(set(found))


def toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, help="exact Codex model id, e.g. gpt-6.1-sol")
    parser.add_argument("--effort", required=True, help="model_reasoning_effort, e.g. low")
    args = parser.parse_args()

    disabled = ",".join(f"{{path={toml_string(path)}, enabled=false}}" for path in user_skill_files())
    prompt = sys.stdin.read()
    with tempfile.TemporaryDirectory(prefix="tui-design-codex-run-") as workdir:
        answer = Path(workdir) / ".answer.txt"
        command = [
            os.environ.get("CODEX_BIN", "codex"),
            "exec",
            "-m", args.model,
            "-c", f'model_reasoning_effort="{args.effort}"',
            "-c", f"skills.config=[{disabled}]",
            "-c", 'web_search="disabled"',
            "--ignore-user-config",
            "--skip-git-repo-check",
            "--ephemeral",
            "-s", "read-only",
            "-C", workdir,
            "--color", "never",
            "-o", str(answer),
            "-",
        ]
        completed = subprocess.run(command, input=prompt, text=True, cwd=workdir, capture_output=True)
        sys.stderr.write(completed.stderr)
        if completed.returncode == 0 and answer.is_file():
            sys.stdout.write(answer.read_text())
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
