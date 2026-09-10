from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS = REPO_ROOT / "scripts/eval_harness.py"
SKILL_RELATIVE = Path("plugins/tui-design/skills/tui-design")
SKILL_DIR = REPO_ROOT / SKILL_RELATIVE
SCHEMA_ROOT_V3 = "https://raw.githubusercontent.com/gfargo/tui-design-skill/main/evals/schema/v3"
RUN_SCHEMA_V3 = f"{SCHEMA_ROOT_V3}/run.schema.json"
GRADES_SCHEMA_V3 = f"{SCHEMA_ROOT_V3}/grades.schema.json"
SUMMARY_SCHEMA_V3 = f"{SCHEMA_ROOT_V3}/summary.schema.json"
SCHEMA_ROOT_V4 = "https://raw.githubusercontent.com/gfargo/tui-design-skill/main/evals/schema/v4"
RUN_SCHEMA_V4 = f"{SCHEMA_ROOT_V4}/run.schema.json"
GRADES_SCHEMA_V4 = f"{SCHEMA_ROOT_V4}/grades.schema.json"
SUMMARY_SCHEMA_V4 = f"{SCHEMA_ROOT_V4}/summary.schema.json"
SCHEMA_ROOT_V5 = "https://raw.githubusercontent.com/gfargo/tui-design-skill/main/evals/schema/v5"
RUN_SCHEMA_V5 = f"{SCHEMA_ROOT_V5}/run.schema.json"
GRADES_SCHEMA_V5 = f"{SCHEMA_ROOT_V5}/grades.schema.json"
SUMMARY_SCHEMA_V5 = f"{SCHEMA_ROOT_V5}/summary.schema.json"
RUN_SCHEMAS = {3: RUN_SCHEMA_V3, 4: RUN_SCHEMA_V4, 5: RUN_SCHEMA_V5}


class EvalHarnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)
        self.eval_set = self.work / "eval.json"
        self.write_eval_set()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def invoke(self, *args: str, expected: int = 0, harness: Path = HARNESS) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [sys.executable, str(harness), *args],
            cwd=harness.parent.parent,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, expected, completed.stderr)
        return completed

    def write_eval_set(self, cases=None) -> None:
        self.eval_set.write_text(
            json.dumps(
                {
                    "skill_name": "tui-design",
                    "evals": cases
                    or [
                        {
                            "id": 7,
                            "name": "small-layout",
                            "prompt": "Review this terminal layout.",
                            "files": [],
                            "assertions": ["Checks narrow behavior", "Cuts duplicate chrome"],
                        }
                    ],
                }
            )
        )

    def write_grading_prompt(self, directory: Path, text: str = "Grading protocol.\n") -> tuple[Path, str]:
        path = directory / "grading-prompt.md"
        path.write_text(text)
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    def downgrade_manifest(self, manifest_path: Path, version: int) -> dict:
        """Rewrite a freshly recorded manifest as an older schema version.

        Older versions never carried skill_invocation_path; their with-skill
        prompts embedded the path without recording it anywhere else.
        """
        manifest = json.loads(manifest_path.read_text())
        manifest["schema_version"] = version
        manifest.pop("skill_invocation_path", None)
        if version >= 3:
            manifest["schema"] = RUN_SCHEMAS[version]
        else:
            for key in ("schema", "runner_version", "generation"):
                manifest.pop(key, None)
        manifest_path.write_text(json.dumps(manifest))
        return manifest

    def make_checkout(self, name: str) -> Path:
        """Copy the harness and skill snapshot to a fresh location, as another machine or CI would have."""
        checkout = self.work / name
        shutil.copytree(SKILL_DIR, checkout / SKILL_RELATIVE)
        (checkout / "scripts").mkdir()
        shutil.copy(HARNESS, checkout / "scripts/eval_harness.py")
        return checkout

    def base_v4_grades(self, manifest, grading_prompt_path: str, digest: str, version: int = 4) -> dict:
        schemas = {4: GRADES_SCHEMA_V4, 5: GRADES_SCHEMA_V5}
        return {
            "schema_version": version,
            "schema": schemas[version],
            "artifact_type": "tui-design-eval-grades",
            "run_id": manifest["run_id"],
            "grader": {
                "kind": "human",
                "name": "Reviewer",
                "prompt_version": "rubric-v1",
                "prompt_sha256": digest,
            },
            "grading_prompt": {"path": grading_prompt_path, "sha256": digest},
            "trials": [
                {
                    "trial_id": manifest["trials"][0]["trial_id"],
                    "assertions": [
                        {"index": 0, "passed": True},
                        {"index": 1, "passed": True},
                    ],
                }
            ],
        }

    def run_fixture(self, run_id: str, runner_code: str, *extra: str, expected: int = 0) -> Path:
        completed = self.invoke(
            "run",
            "--eval-set",
            str(self.eval_set),
            "--condition",
            "with-skill",
            "--provider",
            "fixture",
            "--model",
            "fixture-model-v1",
            "--runner-version",
            "Python " + sys.version.split()[0],
            "--output-dir",
            str(self.work / "runs"),
            "--run-id",
            run_id,
            *extra,
            "--",
            sys.executable,
            "-c",
            runner_code,
            expected=expected,
        )
        return Path(completed.stdout.strip())

    def test_run_score_validate_and_detect_tampering(self) -> None:
        runs = self.work / "runs"
        echo_runner = "import sys; print('ANSWER\\n' + sys.stdin.read(), end='')"
        completed = self.invoke(
            "run",
            "--eval-set",
            str(self.eval_set),
            "--condition",
            "with-skill",
            "--provider",
            "fixture",
            "--model",
            "fixture-model-v1",
            "--runner-version",
            "Python " + sys.version.split()[0],
            "--output-dir",
            str(runs),
            "--run-id",
            "test-run",
            "--repeat",
            "2",
            "--",
            sys.executable,
            "-c",
            echo_runner,
        )
        manifest_path = Path(completed.stdout.strip())
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["model"], "fixture-model-v1")
        self.assertEqual(manifest["provider"], "fixture")
        self.assertEqual(manifest["schema_version"], 5)
        self.assertEqual(manifest["schema"], RUN_SCHEMA_V5)
        self.assertEqual(manifest["skill_invocation_path"], str(SKILL_DIR))
        self.assertEqual(manifest["runner_version"], "Python " + sys.version.split()[0])
        self.assertEqual(manifest["generation"]["system_prompt"]["status"], "unavailable")
        self.assertIsNone(manifest["runner_argv"])
        self.assertFalse(manifest["runner_argv_recorded"])
        self.assertEqual(len(manifest["runner_argv_sha256"]), 64)
        self.assertEqual(len(manifest["trials"]), 2)
        prompt = manifest_path.parent.joinpath(manifest["trials"][0]["prompt_file"]).read_text()
        self.assertTrue(prompt.startswith(f"Use $tui-design at {SKILL_DIR} to solve this request:\n\n"))
        response = manifest_path.parent.joinpath(manifest["trials"][0]["response_file"])
        self.assertIn("ANSWER\nUse $tui-design", response.read_text())

        _, grading_prompt_digest = self.write_grading_prompt(manifest_path.parent)
        grades = {
            "schema_version": 5,
            "schema": GRADES_SCHEMA_V5,
            "artifact_type": "tui-design-eval-grades",
            "run_id": "test-run",
            "grader": {
                "kind": "human",
                "name": "Test Reviewer",
                "prompt_version": "rubric-v1",
                "prompt_sha256": grading_prompt_digest,
            },
            "grading_prompt": {"path": "grading-prompt.md", "sha256": grading_prompt_digest},
            "trials": [
                {
                    "trial_id": trial["trial_id"],
                    "assertions": [
                        {"index": 0, "passed": True, "notes": "present"},
                        {"index": 1, "passed": trial["repetition"] == 1, "notes": "checked"},
                    ],
                }
                for trial in manifest["trials"]
            ],
        }
        grades_path = manifest_path.parent / "grades.json"
        grades_path.write_text(json.dumps(grades))
        summary_path = manifest_path.parent / "summary.json"
        self.invoke("score", "--run", str(manifest_path), "--grades", str(grades_path), "--output", str(summary_path))
        summary = json.loads(summary_path.read_text())
        self.assertEqual((summary["passed"], summary["total"], summary["pass_rate"]), (3, 4, 0.75))
        self.assertEqual(summary["schema"], SUMMARY_SCHEMA_V5)
        self.invoke(
            "validate",
            "--run",
            str(manifest_path),
            "--grades",
            str(grades_path),
            "--summary",
            str(summary_path),
            "--require-completed",
        )

        summary["passed"] = 4
        summary_path.write_text(json.dumps(summary))
        self.invoke(
            "validate",
            "--run",
            str(manifest_path),
            "--grades",
            str(grades_path),
            "--summary",
            str(summary_path),
            expected=2,
        )

        response.write_text(response.read_text() + "tampered")
        self.invoke("validate", "--run", str(manifest_path), expected=2)

    def test_prepare_only_baseline_keeps_raw_prompt(self) -> None:
        completed = self.invoke(
            "run",
            "--eval-set",
            str(self.eval_set),
            "--condition",
            "baseline",
            "--provider",
            "manual",
            "--model",
            "recorded-model-name",
            "--output-dir",
            str(self.work / "prepared"),
            "--run-id",
            "baseline-prepared",
            "--prepare-only",
        )
        manifest_path = Path(completed.stdout.strip())
        manifest = json.loads(manifest_path.read_text())
        prompt = manifest_path.parent.joinpath(manifest["trials"][0]["prompt_file"]).read_text()
        self.assertEqual(prompt, "Review this terminal layout.\n")
        self.assertEqual(manifest["status"], "prepared")
        self.assertIsNone(manifest["skill_invocation_path"])
        self.invoke("validate", "--run", str(manifest_path))
        self.invoke("validate", "--run", str(manifest_path), "--recorded-skill-path", str(SKILL_DIR), expected=2)

    def test_rejects_unsafe_eval_ids_before_creating_a_run(self) -> None:
        for case_id in ("../../escaped", "a b", "..", "/absolute"):
            with self.subTest(case_id=case_id):
                self.write_eval_set(
                    [
                        {
                            "id": case_id,
                            "name": "unsafe",
                            "prompt": "Review this.",
                            "assertions": ["Safe"],
                        }
                    ]
                )
                self.invoke(
                    "run",
                    "--eval-set",
                    str(self.eval_set),
                    "--condition",
                    "baseline",
                    "--provider",
                    "fixture",
                    "--model",
                    "fixture-model-v1",
                    "--output-dir",
                    str(self.work / "unsafe-runs"),
                    "--prepare-only",
                    expected=2,
                )
        self.assertFalse((self.work / "escaped-r1.md").exists())

    def test_validate_reconstructs_complete_trial_set(self) -> None:
        manifest_path = self.run_fixture(
            "coverage-run",
            "import sys; print(sys.stdin.read(), end='')",
            "--repeat",
            "2",
        )
        manifest = json.loads(manifest_path.read_text())
        manifest["trials"].pop()
        manifest_path.write_text(json.dumps(manifest))
        self.invoke("validate", "--run", str(manifest_path), "--require-completed", expected=2)

    def test_completed_run_cannot_contain_prepared_trials(self) -> None:
        completed = self.invoke(
            "run",
            "--eval-set",
            str(self.eval_set),
            "--condition",
            "baseline",
            "--provider",
            "manual",
            "--model",
            "fixture-model-v1",
            "--runner-version",
            "planned-runner-v1",
            "--output-dir",
            str(self.work / "prepared-state"),
            "--run-id",
            "false-complete",
            "--prepare-only",
        )
        manifest_path = Path(completed.stdout.strip())
        manifest = json.loads(manifest_path.read_text())
        manifest["status"] = "completed"
        manifest["completed_at"] = "2026-08-18T00:00:00Z"
        manifest_path.write_text(json.dumps(manifest))
        self.invoke("validate", "--run", str(manifest_path), "--require-completed", expected=2)

    def test_empty_success_is_a_failed_trial(self) -> None:
        manifest_path = self.run_fixture("empty-run", "pass", expected=1)
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["status"], "failed")
        self.assertEqual(manifest["trials"][0]["failure_kind"], "empty_output")
        self.invoke("validate", "--run", str(manifest_path))
        self.invoke("validate", "--run", str(manifest_path), "--require-completed", expected=2)

    def test_timeout_with_partial_bytes_is_finalized(self) -> None:
        manifest_path = self.run_fixture(
            "timeout-run",
            "import os, time; os.write(1, b'PARTIAL'); time.sleep(5)",
            "--timeout",
            "0.5",
            expected=1,
        )
        manifest = json.loads(manifest_path.read_text())
        trial = manifest["trials"][0]
        self.assertEqual((manifest["status"], trial["status"]), ("failed", "timed_out"))
        response = manifest_path.parent / trial["response_file"]
        self.assertEqual(response.read_text(), "PARTIAL")
        self.invoke("validate", "--run", str(manifest_path))

    def test_missing_runner_is_recorded_as_terminal_error(self) -> None:
        completed = self.invoke(
            "run",
            "--eval-set",
            str(self.eval_set),
            "--condition",
            "baseline",
            "--provider",
            "fixture",
            "--model",
            "fixture-model-v1",
            "--runner-version",
            "missing-runner-v1",
            "--output-dir",
            str(self.work / "missing-runner"),
            "--run-id",
            "missing-runner",
            "--",
            str(self.work / "does-not-exist"),
            expected=1,
        )
        manifest_path = Path(completed.stdout.strip())
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["status"], "failed")
        self.assertEqual(manifest["trials"][0]["status"], "error")
        self.invoke("validate", "--run", str(manifest_path))

    def test_runner_arguments_are_recorded_only_on_opt_in(self) -> None:
        manifest_path = self.run_fixture(
            "argv-run",
            "print('ok')",
            "--record-runner-argv",
        )
        manifest = json.loads(manifest_path.read_text())
        self.assertTrue(manifest["runner_argv_recorded"])
        self.assertEqual(manifest["runner_argv"][0], sys.executable)
        self.assertIn("print('ok')", manifest["runner_argv"])

    def test_generation_provenance_records_hashes_not_prompt_contents(self) -> None:
        system_prompt = self.work / "system prompt.txt"
        system_prompt.write_text("private system instructions\n")
        manifest_path = self.run_fixture(
            "provenance-run",
            "print('ok')",
            "--seed",
            "42",
            "--temperature",
            "0.25",
            "--system-prompt-file",
            str(system_prompt),
        )
        manifest_text = manifest_path.read_text()
        manifest = json.loads(manifest_text)
        generation = manifest["generation"]
        self.assertEqual((generation["seed"], generation["temperature"]), (42, 0.25))
        self.assertEqual(generation["system_prompt"]["status"], "recorded")
        self.assertEqual(
            generation["system_prompt"]["sha256"],
            hashlib.sha256(system_prompt.read_bytes()).hexdigest(),
        )
        self.assertEqual(generation["system_prompt"]["bytes"], len(system_prompt.read_bytes()))
        self.assertNotIn(str(system_prompt), manifest_text)
        self.assertNotIn("private system instructions", manifest_text)
        self.invoke("validate", "--run", str(manifest_path), "--require-completed")
        manifest["generation"]["seed"] = True
        manifest_path.write_text(json.dumps(manifest))
        self.invoke("validate", "--run", str(manifest_path), expected=2)

    def test_missing_system_prompt_fails_before_run_directory_creation(self) -> None:
        output_dir = self.work / "missing-system-prompt"
        self.invoke(
            "run",
            "--eval-set",
            str(self.eval_set),
            "--condition",
            "baseline",
            "--provider",
            "fixture",
            "--model",
            "fixture-model-v1",
            "--runner-version",
            "fixture-runner-v1",
            "--output-dir",
            str(output_dir),
            "--run-id",
            "missing-system-prompt",
            "--system-prompt-file",
            str(self.work / "does-not-exist.txt"),
            "--",
            sys.executable,
            "-c",
            "print('ok')",
            expected=2,
        )
        self.assertFalse(output_dir.exists())

    def test_executed_runs_require_runner_version(self) -> None:
        self.invoke(
            "run",
            "--eval-set",
            str(self.eval_set),
            "--condition",
            "baseline",
            "--provider",
            "fixture",
            "--model",
            "fixture-model-v1",
            "--output-dir",
            str(self.work / "no-version"),
            "--",
            sys.executable,
            "-c",
            "print('ok')",
            expected=2,
        )

    def test_schema_v2_artifacts_remain_valid(self) -> None:
        manifest_path = self.run_fixture("legacy-run", "print('ok')")
        manifest = self.downgrade_manifest(manifest_path, 2)
        grades = {
            "schema_version": 2,
            "artifact_type": "tui-design-eval-grades",
            "run_id": manifest["run_id"],
            "grader": {"kind": "human", "name": "Reviewer", "prompt_version": "rubric-v1"},
            "trials": [
                {
                    "trial_id": manifest["trials"][0]["trial_id"],
                    "assertions": [
                        {"index": 0, "passed": True},
                        {"index": 1, "passed": True},
                    ],
                }
            ],
        }
        grades_path = manifest_path.parent / "grades.json"
        grades_path.write_text(json.dumps(grades))
        summary_path = manifest_path.parent / "summary.json"
        self.invoke("score", "--run", str(manifest_path), "--grades", str(grades_path), "--output", str(summary_path))
        summary = json.loads(summary_path.read_text())
        self.assertEqual(summary["schema_version"], 2)
        self.assertNotIn("schema", summary)
        self.invoke(
            "validate",
            "--run",
            str(manifest_path),
            "--grades",
            str(grades_path),
            "--summary",
            str(summary_path),
            "--require-completed",
        )

    def test_grades_require_a_prompt_version(self) -> None:
        manifest_path = self.run_fixture("grader-run", "print('ok')")
        manifest = json.loads(manifest_path.read_text())
        grades = {
            "schema_version": 4,
            "schema": GRADES_SCHEMA_V4,
            "artifact_type": "tui-design-eval-grades",
            "run_id": manifest["run_id"],
            "grader": {"kind": "human", "name": "Reviewer"},
            "trials": [
                {
                    "trial_id": manifest["trials"][0]["trial_id"],
                    "assertions": [
                        {"index": 0, "passed": True},
                        {"index": 1, "passed": True},
                    ],
                }
            ],
        }
        grades_path = manifest_path.parent / "grades.json"
        grades_path.write_text(json.dumps(grades))
        self.invoke("validate", "--run", str(manifest_path), "--grades", str(grades_path), expected=2)

    def test_schema_v3_grades_require_prompt_hash_and_model_provenance(self) -> None:
        manifest_path = self.run_fixture("model-grader-run", "print('ok')")
        manifest = self.downgrade_manifest(manifest_path, 3)
        grades = {
            "schema_version": 3,
            "schema": GRADES_SCHEMA_V3,
            "artifact_type": "tui-design-eval-grades",
            "run_id": manifest["run_id"],
            "grader": {
                "kind": "human",
                "name": "Reviewer",
                "prompt_version": "rubric-v1",
            },
            "trials": [
                {
                    "trial_id": manifest["trials"][0]["trial_id"],
                    "assertions": [
                        {"index": 0, "passed": True},
                        {"index": 1, "passed": True},
                    ],
                }
            ],
        }
        grades_path = manifest_path.parent / "grades.json"
        grades_path.write_text(json.dumps(grades))
        self.invoke("validate", "--run", str(manifest_path), "--grades", str(grades_path), expected=2)

        grades["grader"].update({"kind": "model", "prompt_sha256": "1" * 64, "model": "grader-model"})
        grades_path.write_text(json.dumps(grades))
        self.invoke("validate", "--run", str(manifest_path), "--grades", str(grades_path), expected=2)

        grades["grader"].update(
            {
                "provider": "fixture",
                "runner_version": "grader-runner-v1",
                "generation": {
                    "seed": None,
                    "temperature": 0,
                    "system_prompt": {"status": "unavailable", "sha256": None, "bytes": None},
                },
            }
        )
        grades_path.write_text(json.dumps(grades))
        self.invoke("validate", "--run", str(manifest_path), "--grades", str(grades_path))

    def test_schema_v4_requires_grading_prompt(self) -> None:
        manifest_path = self.run_fixture("v4-grading-prompt-required", "print('ok')")
        manifest = self.downgrade_manifest(manifest_path, 4)
        grades = {
            "schema_version": 4,
            "schema": GRADES_SCHEMA_V4,
            "artifact_type": "tui-design-eval-grades",
            "run_id": manifest["run_id"],
            "grader": {
                "kind": "human",
                "name": "Reviewer",
                "prompt_version": "rubric-v1",
                "prompt_sha256": "1" * 64,
            },
            "trials": [
                {
                    "trial_id": manifest["trials"][0]["trial_id"],
                    "assertions": [
                        {"index": 0, "passed": True},
                        {"index": 1, "passed": True},
                    ],
                }
            ],
        }
        grades_path = manifest_path.parent / "grades.json"
        grades_path.write_text(json.dumps(grades))
        self.invoke("validate", "--run", str(manifest_path), "--grades", str(grades_path), expected=2)

    def test_schema_v4_grading_prompt_rejects_path_traversal(self) -> None:
        manifest_path = self.run_fixture("v4-grading-prompt-traversal", "print('ok')")
        manifest = self.downgrade_manifest(manifest_path, 4)
        outside = self.work / "outside-prompt.md"
        outside.write_text("Escaped prompt.\n")
        digest = hashlib.sha256(outside.read_bytes()).hexdigest()
        grades = self.base_v4_grades(manifest, "../outside-prompt.md", digest)
        grades_path = manifest_path.parent / "grades.json"
        grades_path.write_text(json.dumps(grades))
        self.invoke("validate", "--run", str(manifest_path), "--grades", str(grades_path), expected=2)

    def test_schema_v4_grading_prompt_rejects_missing_file(self) -> None:
        manifest_path = self.run_fixture("v4-grading-prompt-missing", "print('ok')")
        manifest = self.downgrade_manifest(manifest_path, 4)
        grades = self.base_v4_grades(manifest, "grading-prompt.md", "2" * 64)
        grades_path = manifest_path.parent / "grades.json"
        grades_path.write_text(json.dumps(grades))
        self.invoke("validate", "--run", str(manifest_path), "--grades", str(grades_path), expected=2)

    def test_schema_v4_grading_prompt_detects_digest_tampering(self) -> None:
        manifest_path = self.run_fixture("v4-grading-prompt-tamper", "print('ok')")
        manifest = self.downgrade_manifest(manifest_path, 4)
        _, digest = self.write_grading_prompt(manifest_path.parent)
        grades = self.base_v4_grades(manifest, "grading-prompt.md", digest)
        grades_path = manifest_path.parent / "grades.json"
        grades_path.write_text(json.dumps(grades))
        self.invoke("validate", "--run", str(manifest_path), "--grades", str(grades_path))

        (manifest_path.parent / "grading-prompt.md").write_text("Tampered protocol.\n")
        self.invoke("validate", "--run", str(manifest_path), "--grades", str(grades_path), expected=2)

    def test_schema_v4_grading_prompt_digest_must_match_grader_prompt_sha256(self) -> None:
        manifest_path = self.run_fixture("v4-grading-prompt-mismatch", "print('ok')")
        manifest = self.downgrade_manifest(manifest_path, 4)
        _, digest = self.write_grading_prompt(manifest_path.parent)
        grades = self.base_v4_grades(manifest, "grading-prompt.md", digest)
        grades["grader"]["prompt_sha256"] = "3" * 64
        grades_path = manifest_path.parent / "grades.json"
        grades_path.write_text(json.dumps(grades))
        self.invoke("validate", "--run", str(manifest_path), "--grades", str(grades_path), expected=2)

    def test_schema_v5_with_skill_bundle_validates_from_another_checkout(self) -> None:
        manifest_path = self.run_fixture("portable-v5", "print('ok')")
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["skill_dir"], SKILL_RELATIVE.as_posix())
        self.assertEqual(manifest["skill_invocation_path"], str(SKILL_DIR))
        _, digest = self.write_grading_prompt(manifest_path.parent)
        grades_path = manifest_path.parent / "grades.json"
        grades_path.write_text(json.dumps(self.base_v4_grades(manifest, "grading-prompt.md", digest, version=5)))
        summary_path = manifest_path.parent / "summary.json"
        self.invoke("score", "--run", str(manifest_path), "--grades", str(grades_path), "--output", str(summary_path))

        elsewhere = self.make_checkout("elsewhere")
        other_harness = elsewhere / "scripts/eval_harness.py"
        self.assertNotEqual(elsewhere / SKILL_RELATIVE, SKILL_DIR)
        validate = (
            "validate",
            "--run",
            str(manifest_path),
            "--grades",
            str(grades_path),
            "--summary",
            str(summary_path),
            "--require-completed",
        )
        self.invoke(*validate, harness=other_harness)
        self.invoke("score", "--run", str(manifest_path), "--grades", str(grades_path), "--output", str(self.work / "again.json"), harness=other_harness)
        # A recorded path that is also passed explicitly must agree with the manifest.
        self.invoke(*validate, "--recorded-skill-path", str(SKILL_DIR), harness=other_harness)
        self.invoke(*validate, "--recorded-skill-path", str(elsewhere / SKILL_RELATIVE), harness=other_harness, expected=2)

        # The recorded path is checked, not trusted: tampering with it or the prompt still fails.
        prompt_path = manifest_path.parent / manifest["trials"][0]["prompt_file"]
        original_prompt = prompt_path.read_text()
        prompt_path.write_text(original_prompt.replace(str(SKILL_DIR), str(elsewhere / SKILL_RELATIVE)))
        self.invoke(*validate, harness=other_harness, expected=2)
        prompt_path.write_text(original_prompt)
        self.invoke(*validate, harness=other_harness)
        for bad_path in ("", "plugins/tui-design/skills/tui-design", "/somewhere/else", None):
            with self.subTest(skill_invocation_path=bad_path):
                tampered = dict(manifest, skill_invocation_path=bad_path)
                manifest_path.write_text(json.dumps(tampered))
                self.invoke("validate", "--run", str(manifest_path), expected=2)
        manifest_path.write_text(json.dumps(manifest))
        del manifest["skill_invocation_path"]
        manifest_path.write_text(json.dumps(manifest))
        self.invoke("validate", "--run", str(manifest_path), expected=2)

    def test_legacy_with_skill_bundle_validates_from_another_checkout_with_recorded_path(self) -> None:
        elsewhere = self.make_checkout("elsewhere")
        other_harness = elsewhere / "scripts/eval_harness.py"
        for version in (2, 3, 4):
            with self.subTest(schema_version=version):
                manifest_path = self.run_fixture(f"legacy-v{version}", "print('ok')")
                manifest = self.downgrade_manifest(manifest_path, version)
                self.assertNotIn("skill_invocation_path", manifest)
                prompt = manifest_path.parent.joinpath(manifest["trials"][0]["prompt_file"]).read_text()
                self.assertTrue(prompt.startswith(f"Use $tui-design at {SKILL_DIR} to solve"))
                run = ("validate", "--run", str(manifest_path), "--require-completed")

                # From the recording checkout the bundle validates as it always did.
                self.invoke(*run)
                # From another checkout the reconstructed prompt embeds a different path.
                completed = self.invoke(*run, harness=other_harness, expected=2)
                self.assertIn("prompt content mismatch", completed.stderr)
                # Supplying the recorded path reconstructs the prompt the run actually used.
                self.invoke(*run, "--recorded-skill-path", str(SKILL_DIR), harness=other_harness)
                completed = self.invoke(*run, "--recorded-skill-path", "/wrong/skill/path", harness=other_harness, expected=2)
                self.assertIn("prompt content mismatch", completed.stderr)
                self.invoke(*run, "--recorded-skill-path", "", harness=other_harness, expected=2)

                # The recorded hashes still guard the prompt file itself.
                prompt_path = manifest_path.parent / manifest["trials"][0]["prompt_file"]
                prompt_path.write_text(prompt.replace("Review this", "Review that"))
                self.invoke(*run, "--recorded-skill-path", str(SKILL_DIR), harness=other_harness, expected=2)
                prompt_path.write_text(prompt)
                manifest["trials"][0]["prompt_sha256"] = "0" * 64
                manifest_path.write_text(json.dumps(manifest))
                completed = self.invoke(*run, "--recorded-skill-path", str(SKILL_DIR), harness=other_harness, expected=2)
                self.assertIn("prompt hash mismatch", completed.stderr)

                # Legacy schema versions never carried the field, so it stays rejected there.
                manifest["trials"][0]["prompt_sha256"] = hashlib.sha256(prompt.encode()).hexdigest()
                manifest["skill_invocation_path"] = str(SKILL_DIR)
                manifest_path.write_text(json.dumps(manifest))
                self.invoke(*run, expected=2)

    def test_source_root_revalidates_against_recorded_snapshot(self) -> None:
        snapshot = self.make_checkout("snapshot")
        snapshot_harness = snapshot / "scripts/eval_harness.py"
        completed = self.invoke(
            "run",
            "--eval-set",
            str(self.eval_set),
            "--condition",
            "with-skill",
            "--provider",
            "fixture",
            "--model",
            "fixture-model-v1",
            "--runner-version",
            "fixture-runner-v1",
            "--output-dir",
            str(self.work / "runs"),
            "--run-id",
            "snapshot-run",
            "--",
            sys.executable,
            "-c",
            "print('ok')",
            harness=snapshot_harness,
        )
        manifest_path = Path(completed.stdout.strip())
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["skill_dir"], SKILL_RELATIVE.as_posix())
        self.assertEqual(manifest["skill_invocation_path"], str((snapshot / SKILL_RELATIVE).resolve()))
        run = ("validate", "--run", str(manifest_path), "--require-completed")
        self.invoke(*run, harness=snapshot_harness)
        # This checkout holds the same skill snapshot, so it validates the bundle unchanged.
        self.invoke(*run)

        # Once the recording checkout's skill moves on, its evidence needs the recorded snapshot.
        skill_file = snapshot / SKILL_RELATIVE / "SKILL.md"
        skill_file.write_text(skill_file.read_text() + "\nLater edit.\n")
        completed = self.invoke(*run, harness=snapshot_harness, expected=2)
        self.assertIn("skill hash does not match", completed.stderr)
        self.invoke(*run, "--source-root", str(REPO_ROOT), harness=snapshot_harness)
        self.invoke(*run, "--source-root", str(snapshot), expected=2)


if __name__ == "__main__":
    unittest.main()
