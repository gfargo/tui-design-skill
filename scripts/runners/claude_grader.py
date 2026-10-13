#!/usr/bin/env python3
"""Grade a completed eval-harness run with Claude Code, writing schema-v5 grades.

For every trial, the grader receives the preserved grading-prompt file, the
case's numbered rubric assertions, and the trial's response, and must return
{"results": [bool, ...]} with one boolean per assertion. It is not told the run's
condition, provider, or model. Each raw grader reply is kept under
grader-responses/ in the run directory for audit, and the grading prompt is
copied into the run directory so the grades link to it (schema v4+).

Usage:
  python3 scripts/runners/claude_grader.py --run evals/runs/RUN/run.json \\
    --grading-prompt evals/grading/v180-direct-rubric-v1.md \\
    --model claude-opus-5-5 --runner-version "Claude Code 2.1.295"
Set CLAUDE_BIN to choose the Claude Code binary (default: `claude` on PATH).
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GRADES_SCHEMA_V5 = "https://raw.githubusercontent.com/gfargo/tui-design-skill/main/evals/schema/v5/grades.schema.json"


def call_grader(command_prefix, text):
    with tempfile.TemporaryDirectory(prefix="tui-design-grade-") as workdir:
        completed = subprocess.run(command_prefix, input=text, text=True, cwd=workdir, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(f"grader exited {completed.returncode}: {completed.stderr[-500:]}")
    return completed.stdout


def parse_results(reply, count):
    match = re.search(r"\{.*\}", reply, flags=re.DOTALL)
    if not match:
        raise ValueError("no JSON object in grader reply")
    results = json.loads(match.group(0)).get("results")
    if not isinstance(results, list) or len(results) != count or not all(isinstance(item, bool) for item in results):
        raise ValueError(f"expected {count} booleans, got {results!r}")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--grading-prompt", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--runner-version", required=True)
    parser.add_argument("--prompt-version", default="v180-direct-rubric-v1")
    args = parser.parse_args()

    run_dir = args.run.resolve().parent
    manifest = json.loads(args.run.read_text())
    eval_set = json.loads((REPO_ROOT / manifest["eval_set"]).read_text())
    cases = {str(case["id"]): case for case in eval_set["evals"]}
    cases.update({case["name"]: case for case in eval_set["evals"]})

    prompt_copy = run_dir / "grading-prompt.md"
    shutil.copyfile(args.grading_prompt, prompt_copy)
    instructions = prompt_copy.read_text()
    digest = hashlib.sha256(prompt_copy.read_bytes()).hexdigest()
    raw_dir = run_dir / "grader-responses"
    raw_dir.mkdir(exist_ok=True)

    command_prefix = [
        os.environ.get("CLAUDE_BIN", "claude"), "-p", "--model", args.model,
        "--disable-slash-commands", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--setting-sources", "project", "--no-session-persistence", "--tools", "", "--output-format", "text",
    ]
    trials = []
    for trial in manifest["trials"]:
        case = cases[str(trial["case_id"])]
        assertions = case["assertions"]
        response = (run_dir / trial["response_file"]).read_text()
        numbered = "\n".join(f"{index + 1}. {text}" for index, text in enumerate(assertions))
        grader_input = (
            f"{instructions}\n\n## Question\n\n{case['prompt']}\n\n## Assertions\n\n{numbered}\n\n"
            f"## Answer to grade\n\n<answer>\n{response}\n</answer>\n"
        )
        last_error = None
        for _attempt in range(3):
            reply = call_grader(command_prefix, grader_input)
            try:
                results = parse_results(reply, len(assertions))
                break
            except ValueError as error:
                last_error = error
        else:
            raise SystemExit(f"{trial['trial_id']}: grader reply unusable after 3 attempts: {last_error}")
        (raw_dir / f"{trial['trial_id']}.json").write_text(reply)
        trials.append(
            {
                "trial_id": trial["trial_id"],
                "assertions": [{"index": index, "passed": passed} for index, passed in enumerate(results)],
            }
        )
        print(f"graded {trial['trial_id']}: {sum(results)}/{len(results)}", file=sys.stderr)

    grades = {
        "schema_version": 5,
        "schema": GRADES_SCHEMA_V5,
        "artifact_type": "tui-design-eval-grades",
        "run_id": manifest["run_id"],
        "grader": {
            "kind": "model",
            "name": f"{args.model} blind rubric grader",
            "prompt_version": args.prompt_version,
            "prompt_sha256": digest,
            "provider": "Anthropic",
            "model": args.model,
            "runner_version": args.runner_version,
            "generation": {"seed": None, "temperature": None, "system_prompt": {"status": "unavailable", "sha256": None, "bytes": None}},
        },
        "grading_prompt": {"path": "grading-prompt.md", "sha256": digest},
        "trials": trials,
    }
    (run_dir / "grades.json").write_text(json.dumps(grades, indent=2) + "\n")
    print(run_dir / "grades.json")


if __name__ == "__main__":
    main()
