from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS = REPO_ROOT / "scripts/eval_harness.py"


class EvalHarnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)
        self.eval_set = self.work / "eval.json"
        self.write_eval_set()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def invoke(self, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [sys.executable, str(HARNESS), *args],
            cwd=REPO_ROOT,
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
        self.assertEqual(manifest["schema_version"], 2)
        self.assertIsNone(manifest["runner_argv"])
        self.assertFalse(manifest["runner_argv_recorded"])
        self.assertEqual(len(manifest["runner_argv_sha256"]), 64)
        self.assertEqual(len(manifest["trials"]), 2)
        prompt = manifest_path.parent.joinpath(manifest["trials"][0]["prompt_file"]).read_text()
        self.assertIn("Use $tui-design at ", prompt)
        response = manifest_path.parent.joinpath(manifest["trials"][0]["response_file"])
        self.assertIn("ANSWER\nUse $tui-design", response.read_text())

        grades = {
            "schema_version": 2,
            "artifact_type": "tui-design-eval-grades",
            "run_id": "test-run",
            "grader": {"kind": "human", "name": "Test Reviewer", "prompt_version": "rubric-v1"},
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
        self.invoke("validate", "--run", str(manifest_path))

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
            "0.05",
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

    def test_grades_require_a_prompt_version(self) -> None:
        manifest_path = self.run_fixture("grader-run", "print('ok')")
        manifest = json.loads(manifest_path.read_text())
        grades = {
            "schema_version": 2,
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


if __name__ == "__main__":
    unittest.main()
