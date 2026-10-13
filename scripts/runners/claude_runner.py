#!/usr/bin/env python3
"""Eval-harness runner for Claude Code: prompt on stdin, final answer on stdout.

Runs `claude -p` from an empty temporary directory with every user-level
source of skill knowledge switched off, so the baseline condition cannot pick
up an installed copy of this skill:

  --disable-slash-commands          no skills (installed or plugin-provided)
  --strict-mcp-config + empty set   no MCP servers
  --setting-sources project         no user settings or hooks (the temp
                                    directory has no project settings)
  --tools / --allowedTools          only Read, Glob, and Grep

A with-skill prompt names the skill directory ("Use $tui-design at <path> to
solve this request:"); that one directory is added with --add-dir so the model
can read it. Baseline prompts name no path and get no extra directory.

Usage (from scripts/eval_harness.py run ... --):
  python3 scripts/runners/claude_runner.py --model claude-opus-5-5
Set CLAUDE_BIN to choose the Claude Code binary (default: `claude` on PATH).
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile

SKILL_PATH = re.compile(r"^Use \$tui-design at (?P<path>.+?) to solve this request:", re.MULTILINE)
TOOLS = "Read,Glob,Grep"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, help="exact Claude model id, e.g. claude-opus-5-5")
    parser.add_argument("--effort", help="optional --effort level")
    args = parser.parse_args()

    prompt = sys.stdin.read()
    command = [
        os.environ.get("CLAUDE_BIN", "claude"),
        "-p",
        "--model", args.model,
        "--disable-slash-commands",
        "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--setting-sources", "project",
        "--no-session-persistence",
        "--tools", TOOLS,
        "--allowedTools", TOOLS,
        "--output-format", "text",
    ]
    if args.effort:
        command += ["--effort", args.effort]
    match = SKILL_PATH.search(prompt)
    if match:
        command += ["--add-dir", match.group("path")]

    with tempfile.TemporaryDirectory(prefix="tui-design-claude-run-") as workdir:
        completed = subprocess.run(command, input=prompt, text=True, cwd=workdir, capture_output=True)
    sys.stderr.write(completed.stderr)
    sys.stdout.write(completed.stdout)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
