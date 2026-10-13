from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts/validate-evidence.sh"
HARNESS = REPO_ROOT / "scripts/eval_harness.py"
GRADES_SCHEMA_V5 = "https://raw.githubusercontent.com/gfargo/tui-design-skill/main/evals/schema/v5/grades.schema.json"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "Fixture",
    "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
    "GIT_COMMITTER_NAME": "Fixture",
    "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
}


@unittest.skipUnless(shutil.which("git"), "git is required")
class ValidateEvidenceTest(unittest.TestCase):
    """Build a one-bundle fixture repository and run the real script against it."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)
        self.repo = self.make_repo("recorded", marker="recorded")
        self.bundle = self.record_bundle(self.repo)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, repo: Path, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            env={**os.environ, **GIT_ENV},
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def make_repo(self, name: str, marker: str) -> Path:
        repo = self.work / name
        (repo / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPT, repo / "scripts/validate-evidence.sh")
        shutil.copy2(HARNESS, repo / "scripts/eval_harness.py")
        skill = Path("plugins/tui-design/skills/tui-design")
        shutil.copytree(REPO_ROOT / skill, repo / skill)
        (repo / "evals").mkdir()
        (repo / "evals/fixture-evals.json").write_text(
            json.dumps(
                {
                    "skill_name": "tui-design",
                    "evals": [
                        {
                            "id": 1,
                            "name": "fixture-case",
                            "prompt": "Review this terminal layout.",
                            "files": [],
                            "assertions": ["Checks narrow behavior", "Cuts duplicate chrome"],
                        }
                    ],
                }
            )
        )
        (repo / "MARKER").write_text(marker + "\n")
        self.git(repo, "init", "-q")
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-q", "-m", f"{marker} fixture")
        return repo

    def record_bundle(self, repo: Path) -> Path:
        completed = subprocess.run(
            [
                sys.executable, str(repo / "scripts/eval_harness.py"), "run",
                "--eval-set", str(repo / "evals/fixture-evals.json"),
                "--condition", "baseline", "--provider", "fixture", "--model", "fixture-model-v1",
                "--runner-version", "Python " + sys.version.split()[0],
                "--output-dir", str(self.work / "staging"), "--run-id", "fixture-run",
                "--", sys.executable, "-c", "print('ok')",
            ],
            cwd=repo, text=True, capture_output=True, check=True,
        )
        staged = Path(completed.stdout.strip()).parent
        manifest = json.loads((staged / "run.json").read_text())
        prompt = staged / "grading-prompt.md"
        prompt.write_text("Grade each assertion directly.\n")
        digest = hashlib.sha256(prompt.read_bytes()).hexdigest()
        grades = {
            "schema_version": 5,
            "schema": GRADES_SCHEMA_V5,
            "artifact_type": "tui-design-eval-grades",
            "run_id": manifest["run_id"],
            "grader": {"kind": "human", "name": "Fixture reviewer", "prompt_version": "fixture-v1", "prompt_sha256": digest},
            "grading_prompt": {"path": "grading-prompt.md", "sha256": digest},
            "trials": [
                {
                    "trial_id": manifest["trials"][0]["trial_id"],
                    "assertions": [{"index": 0, "passed": True}, {"index": 1, "passed": False}],
                }
            ],
        }
        (staged / "grades.json").write_text(json.dumps(grades))
        subprocess.run(
            [sys.executable, str(repo / "scripts/eval_harness.py"), "score", "--run", str(staged / "run.json"),
             "--grades", str(staged / "grades.json"), "--output", str(staged / "summary.json")],
            cwd=repo, text=True, capture_output=True, check=True,
        )
        return staged

    def install_bundle(self, repo: Path) -> None:
        target = repo / "evals/results/fixture/fixture-run"
        shutil.copytree(self.bundle, target)

    def run_script(self, repo: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(repo / "scripts/validate-evidence.sh")], cwd=repo, text=True, capture_output=True, check=False
        )

    def test_bundle_validates_against_its_recorded_commit(self) -> None:
        self.install_bundle(self.repo)
        completed = self.run_script(self.repo)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Validated 1 evidence bundles", completed.stdout)

    def test_missing_recorded_commit_fails_with_a_clear_error(self) -> None:
        other = self.make_repo("unrelated", marker="unrelated")
        self.install_bundle(other)
        completed = self.run_script(other)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("which is not in this repository", completed.stderr)

    def test_no_bundles_is_an_error(self) -> None:
        completed = self.run_script(self.repo)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("no evidence bundles found", completed.stderr)


if __name__ == "__main__":
    unittest.main()
