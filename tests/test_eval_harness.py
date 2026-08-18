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
        self.eval_set.write_text(
            json.dumps(
                {
                    "skill_name": "tui-design",
                    "evals": [
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
        self.assertEqual(len(manifest["trials"]), 2)
        prompt = manifest_path.parent.joinpath(manifest["trials"][0]["prompt_file"]).read_text()
        self.assertIn("Use $tui-design at ", prompt)
        response = manifest_path.parent.joinpath(manifest["trials"][0]["response_file"])
        self.assertIn("ANSWER\nUse $tui-design", response.read_text())

        grades = {
            "schema_version": 1,
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


if __name__ == "__main__":
    unittest.main()
