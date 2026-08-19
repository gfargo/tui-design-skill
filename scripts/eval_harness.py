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
import math
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional, Sequence


SCHEMA_VERSION = 4
SUPPORTED_SCHEMA_VERSIONS = {2, 3, 4}
SCHEMA_ROOTS = {
    3: "https://raw.githubusercontent.com/gfargo/tui-design-skill/main/evals/schema/v3",
    4: "https://raw.githubusercontent.com/gfargo/tui-design-skill/main/evals/schema/v4",
}
SCHEMA_FILES = {
    "tui-design-eval-run": "run.schema.json",
    "tui-design-eval-grades": "grades.schema.json",
    "tui-design-eval-summary": "summary.schema.json",
}
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKILL_DIR = REPO_ROOT / "plugins/tui-design/skills/tui-design"
CASE_ID_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,127})\Z")
TERMINAL_TRIAL_STATUSES = {"completed", "failed", "timed_out", "error", "aborted"}


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


def schema_uri(artifact_type: str, version: int) -> str:
    root = SCHEMA_ROOTS.get(version)
    if root is None:
        raise HarnessError(f"schema version {version} has no published schema root")
    return f"{root}/{SCHEMA_FILES[artifact_type]}"


def artifact_schema_version(artifact: dict[str, Any], artifact_type: str) -> int:
    version = artifact.get("schema_version")
    if isinstance(version, bool) or not isinstance(version, int) or version not in SUPPORTED_SCHEMA_VERSIONS:
        raise HarnessError(f"{artifact_type} has an unsupported schema version")
    if artifact.get("artifact_type") != artifact_type:
        raise HarnessError(f"artifact is not {artifact_type}")
    if version >= 3 and artifact.get("schema") != schema_uri(artifact_type, version):
        raise HarnessError(f"{artifact_type} does not declare the canonical schema-v{version} URI")
    return version


def load_eval_set(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if not isinstance(data, dict) or data.get("skill_name") != "tui-design":
        raise HarnessError(f"{path} is not a tui-design eval set")
    cases = data.get("evals")
    if not isinstance(cases, list) or not cases:
        raise HarnessError(f"{path} must contain a non-empty 'evals' list; trigger query sets are not response evals")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or case.get("id") is None or isinstance(case.get("id"), bool):
            raise HarnessError(f"eval case in {path} has no valid id")
        case_id = str(case["id"])
        if not CASE_ID_PATTERN.fullmatch(case_id) or case_id in {".", ".."}:
            raise HarnessError(
                f"eval id {case_id!r} must be 1-128 ASCII letters, digits, dots, underscores, or hyphens, "
                "starting with a letter or digit"
            )
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


def resolve_bundle_path(root_dir: Path, value: str, label: str) -> Path:
    """Resolve a recorded evidence-bundle path and prove it remains under root_dir."""
    if not isinstance(value, str) or not value:
        raise HarnessError(f"{label} must be a non-empty relative path")
    recorded = Path(value)
    if recorded.is_absolute():
        raise HarnessError(f"{label} must be relative to its bundle directory: {value!r}")
    bundle_root = root_dir.resolve()
    resolved = (bundle_root / recorded).resolve()
    try:
        resolved.relative_to(bundle_root)
    except ValueError as exc:
        raise HarnessError(f"{label} escapes its bundle directory: {value!r}") from exc
    return resolved


def process_text(value: Any) -> str:
    """Normalize subprocess output, including TimeoutExpired's possible bytes."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def runner_fingerprint(runner: Sequence[str]) -> str:
    encoded = json.dumps(list(runner), ensure_ascii=False, separators=(",", ":")).encode()
    return sha256_bytes(encoded)


def generation_metadata(args: argparse.Namespace) -> dict[str, Any]:
    if args.system_prompt_file:
        system_prompt = Path(args.system_prompt_file).resolve().read_bytes()
        prompt_metadata = {
            "status": "recorded",
            "sha256": sha256_bytes(system_prompt),
            "bytes": len(system_prompt),
        }
    else:
        prompt_metadata = {
            "status": "none" if args.no_system_prompt else "unavailable",
            "sha256": None,
            "bytes": None,
        }
    return {
        "seed": args.seed,
        "temperature": args.temperature,
        "system_prompt": prompt_metadata,
    }


def validate_generation_metadata(value: Any, label: str) -> None:
    if not isinstance(value, dict):
        raise HarnessError(f"{label} must be an object")
    seed = value.get("seed")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
        raise HarnessError(f"{label}.seed must be an integer or null")
    temperature = value.get("temperature")
    if temperature is not None and (
        isinstance(temperature, bool)
        or not isinstance(temperature, (int, float))
        or not math.isfinite(temperature)
        or temperature < 0
    ):
        raise HarnessError(f"{label}.temperature must be a finite non-negative number or null")
    system_prompt = value.get("system_prompt")
    if not isinstance(system_prompt, dict) or system_prompt.get("status") not in {"recorded", "none", "unavailable"}:
        raise HarnessError(f"{label}.system_prompt has an invalid status")
    digest = system_prompt.get("sha256")
    byte_count = system_prompt.get("bytes")
    if system_prompt["status"] == "recorded":
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise HarnessError(f"{label}.system_prompt.sha256 must be a lowercase SHA-256 digest")
        if isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count < 0:
            raise HarnessError(f"{label}.system_prompt.bytes must be a non-negative integer")
    elif digest is not None or byte_count is not None:
        raise HarnessError(f"{label}.system_prompt cannot record a hash or length for this status")


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
    generation = generation_metadata(args)

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
        for repetition in range(1, args.repeat + 1):
            trial_id = f"{case_id}-r{repetition}"
            prompt = invocation_prompt(case["prompt"], args.condition, skill_dir)
            prompt_path = prompt_dir / f"{trial_id}.txt"
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
        "schema": schema_uri("tui-design-eval-run", SCHEMA_VERSION),
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
        "runner_executable": Path(runner[0]).name if runner else None,
        "runner_version": args.runner_version,
        "runner_argv": runner if runner and args.record_runner_argv else None,
        "runner_argv_recorded": bool(runner and args.record_runner_argv),
        "runner_argv_sha256": runner_fingerprint(runner) if runner else None,
        "generation": generation,
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

    def finish_trial(
        trial: dict[str, Any],
        *,
        status: str,
        started: dt.datetime,
        stdout: Any,
        stderr: Any,
        exit_code: Optional[int],
        failure_kind: Optional[str] = None,
    ) -> None:
        response_path = response_dir / f"{trial['trial_id']}.md"
        stderr_path = stderr_dir / f"{trial['trial_id']}.txt"
        response_path.write_text(process_text(stdout))
        stderr_path.write_text(process_text(stderr))
        values: dict[str, Any] = {
            "status": status,
            "exit_code": exit_code,
            "duration_seconds": round((dt.datetime.now(dt.timezone.utc) - started).total_seconds(), 6),
            "response_file": response_path.relative_to(run_dir).as_posix(),
            "response_sha256": sha256_file(response_path),
            "stderr_file": stderr_path.relative_to(run_dir).as_posix(),
            "stderr_sha256": sha256_file(stderr_path),
        }
        if failure_kind:
            values["failure_kind"] = failure_kind
        trial.update(values)

    failures = 0
    for index, trial in enumerate(trials):
        prompt_path = resolve_bundle_path(run_dir, trial["prompt_file"], "prompt_file")
        started = dt.datetime.now(dt.timezone.utc)
        trial["status"] = "running"
        write_json(manifest_path, manifest)
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
            empty_output = completed.returncode == 0 and not completed.stdout.strip()
            finish_trial(
                trial,
                status="completed" if completed.returncode == 0 and not empty_output else "failed",
                started=started,
                stdout=completed.stdout,
                stderr=completed.stderr,
                exit_code=completed.returncode,
                failure_kind="empty_output" if empty_output else ("nonzero_exit" if completed.returncode else None),
            )
            if completed.returncode or empty_output:
                failures += 1
        except subprocess.TimeoutExpired as exc:
            finish_trial(
                trial,
                status="timed_out",
                started=started,
                stdout=exc.stdout,
                stderr=exc.stderr,
                exit_code=None,
                failure_kind="timeout",
            )
            failures += 1
        except OSError as exc:
            finish_trial(
                trial,
                status="error",
                started=started,
                stdout="",
                stderr=f"{type(exc).__name__}: {exc}\n",
                exit_code=None,
                failure_kind="runner_os_error",
            )
            failures += 1
        except KeyboardInterrupt:
            finish_trial(
                trial,
                status="aborted",
                started=started,
                stdout="",
                stderr="evaluation interrupted\n",
                exit_code=None,
                failure_kind="interrupted",
            )
            for remaining in trials[index + 1 :]:
                finish_trial(
                    remaining,
                    status="aborted",
                    started=dt.datetime.now(dt.timezone.utc),
                    stdout="",
                    stderr="not started because evaluation was interrupted\n",
                    exit_code=None,
                    failure_kind="not_started",
                )
            manifest["completed_at"] = utc_now()
            manifest["status"] = "aborted"
            write_json(manifest_path, manifest)
            print(manifest_path)
            return 130
        write_json(manifest_path, manifest)

    manifest["completed_at"] = utc_now()
    manifest["status"] = "failed" if failures else "completed"
    write_json(manifest_path, manifest)
    print(manifest_path)
    return 1 if failures else 0


def expected_trials(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    eval_path = resolve_recorded_path(manifest["eval_set"])
    eval_set = load_eval_set(eval_path)
    repetitions = manifest.get("repetitions")
    if not isinstance(repetitions, int) or isinstance(repetitions, bool) or repetitions < 1:
        raise HarnessError("run manifest repetitions must be a positive integer")
    condition = manifest.get("condition")
    if condition not in {"baseline", "with-skill"}:
        raise HarnessError("run manifest has an invalid condition")
    skill_dir = resolve_recorded_path(manifest["skill_dir"])
    expected: dict[str, dict[str, Any]] = {}
    for case in eval_set["evals"]:
        case_id = str(case["id"])
        for repetition in range(1, repetitions + 1):
            trial_id = f"{case_id}-r{repetition}"
            expected[trial_id] = {
                "trial_id": trial_id,
                "case_id": case_id,
                "case_name": case.get("name"),
                "repetition": repetition,
                "assertion_count": len(case["assertions"]),
                "prompt_file": f"prompts/{trial_id}.txt",
                "prompt": invocation_prompt(case["prompt"], condition, skill_dir),
                "response_file": f"responses/{trial_id}.md",
                "stderr_file": f"stderr/{trial_id}.txt",
            }
    return expected


def expected_trial_assertions(manifest: dict[str, Any]) -> dict[str, int]:
    return {trial_id: trial["assertion_count"] for trial_id, trial in expected_trials(manifest).items()}


def validate_grading_prompt(grades: dict[str, Any], grader: dict[str, Any], grades_path: Path) -> None:
    grading_prompt = grades.get("grading_prompt")
    if not isinstance(grading_prompt, dict):
        raise HarnessError("schema-v4 grades must record grading_prompt")
    digest = grading_prompt.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise HarnessError("grading_prompt.sha256 must be a lowercase SHA-256 digest")
    if digest != grader.get("prompt_sha256"):
        raise HarnessError("grading_prompt.sha256 must match grader.prompt_sha256")
    resolved = resolve_bundle_path(grades_path.parent, grading_prompt.get("path"), "grading_prompt.path")
    if not resolved.is_file():
        raise HarnessError(f"grading_prompt file not found: {grading_prompt.get('path')!r}")
    if sha256_file(resolved) != digest:
        raise HarnessError("grading_prompt file does not match its recorded digest")


def validate_grades(manifest: dict[str, Any], grades: dict[str, Any], grades_path: Path) -> None:
    manifest_version = artifact_schema_version(manifest, "tui-design-eval-run")
    grades_version = artifact_schema_version(grades, "tui-design-eval-grades")
    if grades_version != manifest_version:
        raise HarnessError("grades schema version does not match the run manifest")
    if grades.get("run_id") != manifest.get("run_id"):
        raise HarnessError("grades run_id does not match the run manifest")
    grader = grades.get("grader")
    if not isinstance(grader, dict) or not grader.get("kind") or not grader.get("name"):
        raise HarnessError("grades must record grader.kind and grader.name")
    if grades_version >= 3 and grader.get("kind") not in {"human", "model"}:
        raise HarnessError("grader.kind must be human or model")
    if not grader.get("prompt_version"):
        raise HarnessError("grades must record grader.prompt_version")
    if grades_version >= 3:
        prompt_digest = grader.get("prompt_sha256")
        if not isinstance(prompt_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", prompt_digest):
            raise HarnessError("schema-v3 grades must record grader.prompt_sha256")
    if grader.get("kind") == "model":
        if not grader.get("model"):
            raise HarnessError("model grading must record grader.model")
        if grades_version >= 3:
            for key in ("provider", "runner_version"):
                if not grader.get(key):
                    raise HarnessError(f"schema-v3 model grading must record grader.{key}")
            validate_generation_metadata(grader.get("generation"), "grader.generation")
    if grades_version >= 4:
        validate_grading_prompt(grades, grader, grades_path)

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


def score_metrics(manifest: dict[str, Any], grades: dict[str, Any]) -> tuple[int, int, list[dict[str, Any]]]:
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
    return passed, total, list(by_case.values())


def command_score(args: argparse.Namespace) -> int:
    manifest_path = Path(args.run).resolve()
    manifest = read_json(manifest_path)
    grades_path = Path(args.grades).resolve()
    grades = read_json(grades_path)
    validate_manifest(manifest_path, manifest, require_completed=True)
    validate_grades(manifest, grades, grades_path)

    version = artifact_schema_version(manifest, "tui-design-eval-run")
    passed, total, by_case = score_metrics(manifest, grades)
    summary = {
        "schema_version": version,
        "artifact_type": "tui-design-eval-summary",
        "run_id": manifest["run_id"],
        "created_at": utc_now(),
        "run_manifest_sha256": sha256_file(manifest_path),
        "grades_file": portable_path(grades_path, manifest_path.parent),
        "grades_sha256": sha256_file(grades_path),
        "passed": passed,
        "total": total,
        "pass_rate": passed / total,
        "by_case": by_case,
    }
    if version >= 3:
        summary["schema"] = schema_uri("tui-design-eval-summary", version)
    output = Path(args.output).resolve() if args.output else manifest_path.parent / "summary.json"
    write_json(output, summary)
    print(output)
    return 0


def validate_manifest(path: Path, manifest: dict[str, Any], require_completed: bool = False) -> None:
    version = artifact_schema_version(manifest, "tui-design-eval-run")
    for key in ("run_id", "condition", "provider", "model", "eval_set", "eval_set_sha256", "skill_dir", "skill_sha256"):
        if not manifest.get(key):
            raise HarnessError(f"run manifest is missing {key}")
    if manifest.get("run_id") != path.parent.name:
        raise HarnessError("run manifest run_id does not match its directory name")
    if require_completed and manifest.get("status") != "completed":
        raise HarnessError(f"run is not completed successfully: {manifest.get('status')!r}")
    if manifest.get("status") not in {"prepared", "running", "completed", "failed", "aborted"}:
        raise HarnessError(f"run manifest has an invalid status: {manifest.get('status')!r}")
    if not isinstance(manifest.get("runner_argv_recorded"), bool):
        raise HarnessError("run manifest must record runner_argv_recorded")
    if manifest["runner_argv_recorded"] != (manifest.get("runner_argv") is not None):
        raise HarnessError("runner_argv_recorded does not match runner_argv presence")
    if manifest["runner_argv_recorded"] and (
        not isinstance(manifest["runner_argv"], list)
        or not all(isinstance(value, str) for value in manifest["runner_argv"])
    ):
        raise HarnessError("runner_argv must be a list of strings when recorded")
    if manifest.get("status") != "prepared" and not manifest.get("runner_argv_sha256"):
        raise HarnessError("executed runs must record runner_argv_sha256")
    if manifest.get("runner_argv_sha256") and not re.fullmatch(r"[0-9a-f]{64}", manifest["runner_argv_sha256"]):
        raise HarnessError("runner_argv_sha256 must be a lowercase SHA-256 digest")
    if version >= 3:
        if manifest.get("status") != "prepared":
            if not isinstance(manifest.get("runner_executable"), str) or not manifest["runner_executable"].strip():
                raise HarnessError("executed schema-v3 runs must record runner_executable")
            if not isinstance(manifest.get("runner_version"), str) or not manifest["runner_version"].strip():
                raise HarnessError("executed schema-v3 runs must record runner_version")
        validate_generation_metadata(manifest.get("generation"), "generation")

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
    if not all(isinstance(trial, dict) for trial in trials):
        raise HarnessError("every run trial must be an object")
    trial_ids = [trial.get("trial_id") for trial in trials]
    if not all(isinstance(trial_id, str) for trial_id in trial_ids):
        raise HarnessError("every run trial must have a string trial_id")
    if len(trial_ids) != len(set(trial_ids)):
        raise HarnessError("run manifest contains duplicate trial ids")
    expected = expected_trials(manifest)
    if set(trial_ids) != set(expected):
        missing = sorted(set(expected) - set(trial_ids))
        extra = sorted(set(trial_ids) - set(expected))
        raise HarnessError(f"run trial coverage mismatch; missing={missing}, extra={extra}")
    actual = {trial["trial_id"]: trial for trial in trials}
    for trial_id, specification in expected.items():
        trial = actual[trial_id]
        for field in ("case_id", "case_name", "repetition", "prompt_file"):
            if trial.get(field) != specification[field]:
                raise HarnessError(f"{field} mismatch for {trial_id}")
        prompt = resolve_bundle_path(run_dir, trial["prompt_file"], f"prompt_file for {trial_id}")
        if prompt.read_text() != specification["prompt"]:
            raise HarnessError(f"prompt content mismatch for {trial_id}")
        if sha256_file(prompt) != trial["prompt_sha256"]:
            raise HarnessError(f"prompt hash mismatch for {trial_id}")
        status = trial.get("status")
        if status not in {"prepared", "running", *TERMINAL_TRIAL_STATUSES}:
            raise HarnessError(f"invalid trial status for {trial_id}: {status!r}")
        if status in TERMINAL_TRIAL_STATUSES:
            if trial.get("response_file") != specification["response_file"]:
                raise HarnessError(f"response_file mismatch for {trial_id}")
            if trial.get("stderr_file") != specification["stderr_file"]:
                raise HarnessError(f"stderr_file mismatch for {trial_id}")
            response = resolve_bundle_path(run_dir, trial["response_file"], f"response_file for {trial_id}")
            stderr = resolve_bundle_path(run_dir, trial["stderr_file"], f"stderr_file for {trial_id}")
            if sha256_file(response) != trial["response_sha256"]:
                raise HarnessError(f"response hash mismatch for {trial_id}")
            if sha256_file(stderr) != trial["stderr_sha256"]:
                raise HarnessError(f"stderr hash mismatch for {trial_id}")
            if status == "completed" and not response.read_text().strip():
                raise HarnessError(f"completed trial has an empty response: {trial_id}")
            if status == "completed" and trial.get("exit_code") != 0:
                raise HarnessError(f"completed trial must have exit_code 0: {trial_id}")

    statuses = {trial["status"] for trial in trials}
    run_status = manifest["status"]
    if run_status == "prepared" and statuses != {"prepared"}:
        raise HarnessError("prepared run must contain only prepared trials")
    if run_status == "completed" and statuses != {"completed"}:
        raise HarnessError("completed run must contain only completed trials")
    if run_status in {"failed", "aborted"} and not statuses.issubset(TERMINAL_TRIAL_STATUSES):
        raise HarnessError(f"{run_status} run must contain only terminal trials")
    if run_status in {"completed", "failed", "aborted"} and not manifest.get("completed_at"):
        raise HarnessError(f"{run_status} run must record completed_at")


def command_validate(args: argparse.Namespace) -> int:
    manifest_path = Path(args.run).resolve()
    manifest = read_json(manifest_path)
    validate_manifest(manifest_path, manifest, require_completed=args.require_completed)

    if args.grades:
        grades_path = Path(args.grades).resolve()
        grades = read_json(grades_path)
        validate_grades(manifest, grades, grades_path)
    else:
        grades_path = None

    if args.summary:
        if grades_path is None:
            raise HarnessError("--summary requires --grades so calculated results can be verified")
        summary_path = Path(args.summary).resolve()
        summary = read_json(summary_path)
        summary_version = artifact_schema_version(summary, "tui-design-eval-summary")
        if summary_version != artifact_schema_version(manifest, "tui-design-eval-run"):
            raise HarnessError("summary schema version does not match the run manifest")
        if summary.get("run_id") != manifest["run_id"]:
            raise HarnessError("summary does not match the run manifest")
        if sha256_file(manifest_path) != summary.get("run_manifest_sha256"):
            raise HarnessError("summary was calculated from a different run manifest")
        if sha256_file(grades_path) != summary.get("grades_sha256"):
            raise HarnessError("summary was calculated from different grades")
        if summary.get("grades_file") != portable_path(grades_path, manifest_path.parent):
            raise HarnessError("summary grades_file does not match the supplied grades")
        expected_passed, expected_total, expected_by_case = score_metrics(manifest, grades)
        expected_values = {
            "passed": expected_passed,
            "total": expected_total,
            "pass_rate": expected_passed / expected_total,
            "by_case": expected_by_case,
        }
        for key, expected in expected_values.items():
            if summary.get(key) != expected:
                raise HarnessError(f"summary {key} does not match the supplied grades")

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
    run.add_argument("--runner-version", help="exact caller-reported version of the model runner")
    run.add_argument("--seed", type=int, help="caller-reported model generation seed, when exposed")
    run.add_argument("--temperature", type=float, help="caller-reported model temperature, when exposed")
    system_prompt = run.add_mutually_exclusive_group()
    system_prompt.add_argument(
        "--system-prompt-file",
        help="system-prompt file used by the runner; records only its SHA-256 and byte length",
    )
    system_prompt.add_argument(
        "--no-system-prompt",
        action="store_true",
        help="record that the runner used no separate system prompt; omission means unavailable",
    )
    run.add_argument("--prepare-only", action="store_true", help="write prompts and manifest without executing a runner")
    run.add_argument(
        "--record-runner-argv",
        action="store_true",
        help="store exact runner arguments in run.json; off by default because arguments may contain secrets",
    )
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
    if getattr(args, "temperature", None) is not None and (
        not math.isfinite(args.temperature) or args.temperature < 0
    ):
        parser.error("--temperature must be a finite non-negative number")
    if getattr(args, "command", None) == "run" and not args.prepare_only and (
        not isinstance(args.runner_version, str) or not args.runner_version.strip()
    ):
        parser.error("--runner-version is required for executed runs")
    try:
        return args.handler(args)
    except (HarnessError, KeyError, OSError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
