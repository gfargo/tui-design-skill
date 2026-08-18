#!/usr/bin/env python3
"""Run, score, and validate reproducible tui-design content evaluations.

The model runner is an arbitrary command that reads one prompt from stdin and
writes one response to stdout. It is executed directly, never through a shell.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional, Sequence


SCHEMA_VERSION = 1
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKILL_DIR = REPO_ROOT / "plugins/tui-design/skills/tui-design"


class HarnessError(RuntimeError):
    """A user-facing validation or execution error."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_tree(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        relative = path.relative_to(directory).as_posix().encode()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def portable_path(path: Path, base: Path = REPO_ROOT) -> str:
    path = path.resolve()
    try:
        return path.relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path)


def resolve_recorded_path(value: str, base: Path = REPO_ROOT) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    os.replace(temporary, path)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError(f"cannot read JSON from {path}: {exc}") from exc


def load_eval_set(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if not isinstance(data, dict) or data.get("skill_name") != "tui-design":
        raise HarnessError(f"{path} is not a tui-design eval set")
    cases = data.get("evals")
    if not isinstance(cases, list) or not cases:
        raise HarnessError(f"{path} must contain a non-empty 'evals' list; trigger query sets are not response evals")
    seen: set[str] = set()
    for case in cases:
        case_id = str(case.get("id"))
        if case_id in seen:
            raise HarnessError(f"duplicate eval id {case_id!r} in {path}")
        seen.add(case_id)
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise HarnessError(f"eval {case_id!r} has no prompt")
        assertions = case.get("assertions")
        if not isinstance(assertions, list) or not assertions or not all(isinstance(item, str) and item.strip() for item in assertions):
            raise HarnessError(f"eval {case_id!r} has invalid assertions")
    return data


def safe_label(value: str) -> str:
    label = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    if not label:
        raise HarnessError(f"value cannot form a safe path label: {value!r}")
    return label


def git_metadata() -> dict[str, Any]:
    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False
        )

    commit = git("rev-parse", "HEAD")
    status = git("status", "--porcelain")
    branch = git("branch", "--show-current")
    if commit.returncode:
        return {"commit": None, "branch": None, "dirty": None}
    return {
        "commit": commit.stdout.strip(),
        "branch": branch.stdout.strip() or None,
        "dirty": bool(status.stdout.strip()),
    }


def host_metadata() -> dict[str, str]:
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
    }


def invocation_prompt(raw_prompt: str, condition: str, skill_dir: Path) -> str:
    if condition == "baseline":
        return raw_prompt.rstrip() + "\n"
    return (
        f"Use $tui-design at {skill_dir.resolve()} to solve this request:\n\n"
        f"{raw_prompt.rstrip()}\n"
    )


def make_run_id(eval_set: Path, condition: str) -> str:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{safe_label(eval_set.stem)}-{condition}"


def normalize_runner(values: Sequence[str]) -> list[str]:
    runner = list(values)
    if runner and runner[0] == "--":
        runner = runner[1:]
    return runner


def command_run(args: argparse.Namespace) -> int:
    eval_path = Path(args.eval_set).resolve()
    skill_dir = Path(args.skill_dir).resolve()
    eval_set = load_eval_set(eval_path)
    if not skill_dir.joinpath("SKILL.md").is_file():
        raise HarnessError(f"skill directory has no SKILL.md: {skill_dir}")

    runner = normalize_runner(args.runner)
    if not args.prepare_only and not runner:
        raise HarnessError("a runner command is required after '--' unless --prepare-only is used")

    run_id = safe_label(args.run_id) if args.run_id else make_run_id(eval_path, args.condition)
    run_dir = Path(args.output_dir).resolve() / run_id
    if run_dir.exists():
        raise HarnessError(f"run directory already exists: {run_dir}")
    prompt_dir = run_dir / "prompts"
    response_dir = run_dir / "responses"
    stderr_dir = run_dir / "stderr"
    prompt_dir.mkdir(parents=True)
    if not args.prepare_only:
        response_dir.mkdir()
        stderr_dir.mkdir()

    created_at = utc_now()
    trials: list[dict[str, Any]] = []
    for case in eval_set["evals"]:
        case_id = str(case["id"])
        case_label = safe_label(case.get("name") or case_id)
        for repetition in range(1, args.repeat + 1):
            trial_id = f"{case_id}-r{repetition}"
            prompt = invocation_prompt(case["prompt"], args.condition, skill_dir)
            prompt_path = prompt_dir / f"{safe_label(case_id)}-{case_label}-r{repetition}.txt"
            prompt_path.write_text(prompt)
            trials.append(
                {
                    "trial_id": trial_id,
                    "case_id": case_id,
                    "case_name": case.get("name"),
                    "repetition": repetition,
                    "prompt_file": prompt_path.relative_to(run_dir).as_posix(),
                    "prompt_sha256": sha256_file(prompt_path),
                    "status": "prepared",
                }
            )

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "tui-design-eval-run",
        "run_id": run_id,
        "status": "prepared" if args.prepare_only else "running",
        "created_at": created_at,
        "completed_at": created_at if args.prepare_only else None,
        "eval_set": portable_path(eval_path),
        "eval_set_sha256": sha256_file(eval_path),
        "skill_dir": portable_path(skill_dir),
        "skill_sha256": sha256_tree(skill_dir),
        "condition": args.condition,
        "provider": args.provider,
        "model": args.model,
        "repetitions": args.repeat,
        "runner_argv": runner or None,
        "timeout_seconds": args.timeout,
        "git": git_metadata(),
        "host": host_metadata(),
        "trials": trials,
    }
    manifest_path = run_dir / "run.json"
    write_json(manifest_path, manifest)

    if args.prepare_only:
        print(manifest_path)
        return 0

    failures = 0
    for trial in trials:
        prompt_path = run_dir / trial["prompt_file"]
        response_path = response_dir / f"{trial['trial_id']}.md"
        stderr_path = stderr_dir / f"{trial['trial_id']}.txt"
        started = dt.datetime.now(dt.timezone.utc)
        environment = os.environ.copy()
        environment.update(
            {
                "TUI_EVAL_RUN_ID": run_id,
                "TUI_EVAL_TRIAL_ID": trial["trial_id"],
                "TUI_EVAL_PROVIDER": args.provider,
                "TUI_EVAL_MODEL": args.model,
            }
        )
        try:
            completed = subprocess.run(
                runner,
                input=prompt_path.read_text(),
                text=True,
                capture_output=True,
                timeout=args.timeout,
                check=False,
                env=environment,
            )
            response_path.write_text(completed.stdout)
            stderr_path.write_text(completed.stderr)
            trial.update(
                {
                    "status": "completed" if completed.returncode == 0 else "failed",
                    "exit_code": completed.returncode,
                    "duration_seconds": round((dt.datetime.now(dt.timezone.utc) - started).total_seconds(), 6),
                    "response_file": response_path.relative_to(run_dir).as_posix(),
                    "response_sha256": sha256_file(response_path),
                    "stderr_file": stderr_path.relative_to(run_dir).as_posix(),
                    "stderr_sha256": sha256_file(stderr_path),
                }
            )
            if completed.returncode:
                failures += 1
        except subprocess.TimeoutExpired as exc:
            response_path.write_text(exc.stdout or "")
            stderr_path.write_text(exc.stderr or "")
            trial.update(
                {
                    "status": "timed_out",
                    "exit_code": None,
                    "duration_seconds": round((dt.datetime.now(dt.timezone.utc) - started).total_seconds(), 6),
                    "response_file": response_path.relative_to(run_dir).as_posix(),
                    "response_sha256": sha256_file(response_path),
                    "stderr_file": stderr_path.relative_to(run_dir).as_posix(),
                    "stderr_sha256": sha256_file(stderr_path),
                }
            )
            failures += 1
        write_json(manifest_path, manifest)

    manifest["completed_at"] = utc_now()
    manifest["status"] = "failed" if failures else "completed"
    write_json(manifest_path, manifest)
    print(manifest_path)
    return 1 if failures else 0


def expected_trial_assertions(manifest: dict[str, Any]) -> dict[str, int]:
    eval_path = resolve_recorded_path(manifest["eval_set"])
    eval_set = load_eval_set(eval_path)
    counts = {str(case["id"]): len(case["assertions"]) for case in eval_set["evals"]}
    return {trial["trial_id"]: counts[trial["case_id"]] for trial in manifest["trials"]}


def validate_grades(manifest: dict[str, Any], grades: dict[str, Any]) -> None:
    if grades.get("schema_version") != SCHEMA_VERSION or grades.get("artifact_type") != "tui-design-eval-grades":
        raise HarnessError("grades have an unsupported schema or artifact type")
    if grades.get("run_id") != manifest.get("run_id"):
        raise HarnessError("grades run_id does not match the run manifest")
    grader = grades.get("grader")
    if not isinstance(grader, dict) or not grader.get("kind") or not grader.get("name"):
        raise HarnessError("grades must record grader.kind and grader.name")
    if grader.get("kind") == "model" and not grader.get("model"):
        raise HarnessError("model grading must record grader.model")

    expected = expected_trial_assertions(manifest)
    items = grades.get("trials")
    if not isinstance(items, list):
        raise HarnessError("grades.trials must be a list")
    actual_ids = [item.get("trial_id") for item in items]
    if len(actual_ids) != len(set(actual_ids)):
        raise HarnessError("grades contain duplicate trial ids")
    if set(actual_ids) != set(expected):
        missing = sorted(set(expected) - set(actual_ids))
        extra = sorted(set(actual_ids) - set(expected))
        raise HarnessError(f"grade coverage mismatch; missing={missing}, extra={extra}")
    for item in items:
        assertions = item.get("assertions")
        if not isinstance(assertions, list) or len(assertions) != expected[item["trial_id"]]:
            raise HarnessError(f"wrong assertion count for {item['trial_id']}")
        indexes = [assertion.get("index") for assertion in assertions if isinstance(assertion, dict)]
        if indexes != list(range(expected[item["trial_id"]])):
            raise HarnessError(f"assertion indexes for {item['trial_id']} must be ordered from zero")
        if not all(isinstance(assertion.get("passed"), bool) for assertion in assertions):
            raise HarnessError(f"every assertion for {item['trial_id']} needs a boolean passed value")


def command_score(args: argparse.Namespace) -> int:
    manifest_path = Path(args.run).resolve()
    manifest = read_json(manifest_path)
    grades_path = Path(args.grades).resolve()
    grades = read_json(grades_path)
    validate_manifest(manifest_path, manifest, require_completed=True)
    validate_grades(manifest, grades)

    case_names = {trial["case_id"]: trial.get("case_name") for trial in manifest["trials"]}
    by_case: dict[str, dict[str, Any]] = {}
    total = passed = 0
    for item in grades["trials"]:
        manifest_trial = next(trial for trial in manifest["trials"] if trial["trial_id"] == item["trial_id"])
        case_id = manifest_trial["case_id"]
        case = by_case.setdefault(
            case_id,
            {"case_id": case_id, "case_name": case_names[case_id], "passed": 0, "total": 0},
        )
        item_total = len(item["assertions"])
        item_passed = sum(assertion["passed"] for assertion in item["assertions"])
        case["total"] += item_total
        case["passed"] += item_passed
        total += item_total
        passed += item_passed

    for case in by_case.values():
        case["pass_rate"] = case["passed"] / case["total"]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "tui-design-eval-summary",
        "run_id": manifest["run_id"],
        "created_at": utc_now(),
        "run_manifest_sha256": sha256_file(manifest_path),
        "grades_file": portable_path(grades_path, manifest_path.parent),
        "grades_sha256": sha256_file(grades_path),
        "passed": passed,
        "total": total,
        "pass_rate": passed / total,
        "by_case": list(by_case.values()),
    }
    output = Path(args.output).resolve() if args.output else manifest_path.parent / "summary.json"
    write_json(output, summary)
    print(output)
    return 0


def validate_manifest(path: Path, manifest: dict[str, Any], require_completed: bool = False) -> None:
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("artifact_type") != "tui-design-eval-run":
        raise HarnessError("run manifest has an unsupported schema or artifact type")
    for key in ("run_id", "condition", "provider", "model", "eval_set", "eval_set_sha256", "skill_dir", "skill_sha256"):
        if not manifest.get(key):
            raise HarnessError(f"run manifest is missing {key}")
    if manifest["condition"] not in {"baseline", "with-skill"}:
        raise HarnessError("run manifest has an invalid condition")
    if require_completed and manifest.get("status") != "completed":
        raise HarnessError(f"run is not completed successfully: {manifest.get('status')!r}")

    eval_path = resolve_recorded_path(manifest["eval_set"])
    skill_dir = resolve_recorded_path(manifest["skill_dir"])
    if sha256_file(eval_path) != manifest["eval_set_sha256"]:
        raise HarnessError("eval-set hash does not match the recorded input")
    if sha256_tree(skill_dir) != manifest["skill_sha256"]:
        raise HarnessError("skill hash does not match the recorded input")

    run_dir = path.parent
    trials = manifest.get("trials")
    if not isinstance(trials, list) or not trials:
        raise HarnessError("run manifest has no trials")
    trial_ids = [trial.get("trial_id") for trial in trials]
    if len(trial_ids) != len(set(trial_ids)):
        raise HarnessError("run manifest contains duplicate trial ids")
    for trial in trials:
        prompt = run_dir / trial["prompt_file"]
        if sha256_file(prompt) != trial["prompt_sha256"]:
            raise HarnessError(f"prompt hash mismatch for {trial['trial_id']}")
        if trial.get("status") in {"completed", "failed", "timed_out"}:
            response = run_dir / trial["response_file"]
            stderr = run_dir / trial["stderr_file"]
            if sha256_file(response) != trial["response_sha256"]:
                raise HarnessError(f"response hash mismatch for {trial['trial_id']}")
            if sha256_file(stderr) != trial["stderr_sha256"]:
                raise HarnessError(f"stderr hash mismatch for {trial['trial_id']}")


def command_validate(args: argparse.Namespace) -> int:
    manifest_path = Path(args.run).resolve()
    manifest = read_json(manifest_path)
    validate_manifest(manifest_path, manifest, require_completed=args.require_completed)

    if args.grades:
        grades_path = Path(args.grades).resolve()
        grades = read_json(grades_path)
        validate_grades(manifest, grades)
    else:
        grades_path = None

    if args.summary:
        summary_path = Path(args.summary).resolve()
        summary = read_json(summary_path)
        if summary.get("artifact_type") != "tui-design-eval-summary" or summary.get("run_id") != manifest["run_id"]:
            raise HarnessError("summary does not match the run manifest")
        if sha256_file(manifest_path) != summary.get("run_manifest_sha256"):
            raise HarnessError("summary was calculated from a different run manifest")
        if grades_path and sha256_file(grades_path) != summary.get("grades_sha256"):
            raise HarnessError("summary was calculated from different grades")

    print(f"Validated {manifest['run_id']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="prepare prompts and optionally execute a model runner")
    run.add_argument("--eval-set", required=True, help="content eval JSON containing an evals list")
    run.add_argument("--condition", choices=("baseline", "with-skill"), required=True)
    run.add_argument("--provider", required=True, help="provider recorded in the run manifest")
    run.add_argument("--model", required=True, help="exact model identifier recorded in the run manifest")
    run.add_argument("--skill-dir", default=str(DEFAULT_SKILL_DIR))
    run.add_argument("--output-dir", default=str(REPO_ROOT / "evals/runs"))
    run.add_argument("--run-id", help="stable output-directory name; default includes the UTC timestamp")
    run.add_argument("--repeat", type=int, default=1)
    run.add_argument("--timeout", type=float, default=600.0)
    run.add_argument("--prepare-only", action="store_true", help="write prompts and manifest without executing a runner")
    run.add_argument("runner", nargs=argparse.REMAINDER, help="command after --; reads prompt on stdin, writes response on stdout")
    run.set_defaults(handler=command_run)

    score = subparsers.add_parser("score", help="validate complete grades and calculate a summary")
    score.add_argument("--run", required=True, help="path to run.json")
    score.add_argument("--grades", required=True, help="path to grades JSON")
    score.add_argument("--output", help="summary path; default is summary.json beside run.json")
    score.set_defaults(handler=command_score)

    validate = subparsers.add_parser("validate", help="validate recorded hashes and optional grading artifacts")
    validate.add_argument("--run", required=True, help="path to run.json")
    validate.add_argument("--grades", help="optional grades JSON")
    validate.add_argument("--summary", help="optional summary JSON")
    validate.add_argument("--require-completed", action="store_true")
    validate.set_defaults(handler=command_validate)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "repeat", 1) < 1:
        parser.error("--repeat must be at least 1")
    if getattr(args, "timeout", 1) <= 0:
        parser.error("--timeout must be positive")
    try:
        return args.handler(args)
    except (HarnessError, KeyError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
