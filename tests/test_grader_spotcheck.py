from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("grader_spotcheck", REPO_ROOT / "scripts/grader_spotcheck.py")
spotcheck = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spotcheck)


def make_bundle(root: Path, run_id: str, claude_passes: list[list[bool]]) -> Path:
    """One case with two assertions and one trial per entry of claude_passes."""
    run_dir = root / run_id
    (run_dir / "responses").mkdir(parents=True)
    trials = []
    for index, _ in enumerate(claude_passes, start=1):
        trial_id = f"case-r{index}"
        (run_dir / "responses" / f"{trial_id}.txt").write_text(f"answer {index}")
        trials.append({"trial_id": trial_id, "case_id": "case", "response_file": f"responses/{trial_id}.txt"})
    (run_dir / "run.json").write_text(json.dumps({"run_id": run_id, "eval_set": "evals/fake.json", "condition": "with-skill",
                                                   "provider": "Anthropic", "trials": trials}))
    (run_dir / "grading-prompt.md").write_text("Grade each assertion.")
    (run_dir / "grades.json").write_text(json.dumps({"grader": {"provider": "Anthropic", "model": "m", "prompt_version": "v1"}, "trials": [
        {"trial_id": f"case-r{i}", "assertions": [{"index": k, "passed": p, "notes": "n"} for k, p in enumerate(row)]}
        for i, row in enumerate(claude_passes, start=1)]}))
    return run_dir


class SpotcheckTest(unittest.TestCase):
    def test_sample_is_deterministic_and_at_least_one(self) -> None:
        trials = [{"trial_id": f"c-r{i}"} for i in range(1, 21)]
        first = spotcheck.sample_trials("run", trials, 0.15, 79)
        self.assertEqual(first, spotcheck.sample_trials("run", trials, 0.15, 79))
        self.assertEqual(len(first), 3)
        self.assertNotEqual(first, spotcheck.sample_trials("run", trials, 0.15, 80))
        self.assertEqual(len(spotcheck.sample_trials("run", trials[:2], 0.01, 79)), 1)

    def test_kappa(self) -> None:
        self.assertAlmostEqual(spotcheck.cohens_kappa([(True, True), (False, False)]), 1.0)
        self.assertAlmostEqual(spotcheck.cohens_kappa([(True, False), (False, True)]), -1.0)
        self.assertIsNone(spotcheck.cohens_kappa([(True, True), (True, True)]))
        self.assertIsNone(spotcheck.cohens_kappa([]))

    def test_summary_counts_agreement_and_pass_rates(self) -> None:
        summary = spotcheck.summarize([(True, True), (True, False), (False, False), (True, True)])
        self.assertEqual((summary["assertions"], summary["agree"]), (4, 3))
        self.assertAlmostEqual(summary["claude_pass_rate"], 0.75)
        self.assertAlmostEqual(summary["codex_pass_rate"], 0.5)

    def test_run_spotcheck_reports_disagreements(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evals").mkdir()
            (root / "evals/fake.json").write_text(json.dumps({"evals": [{"id": "case", "name": "case", "prompt": "Q?", "assertions": ["A one", "A two"]}]}))
            run_dir = make_bundle(root, "bundle", [[True, True], [True, False]])
            spotcheck.REPO_ROOT = root
            replies = iter(['{"results": [{"passed": true, "note": "ok"}, {"passed": false, "note": "no"}]}'] * 2)
            report = spotcheck.run_spotcheck([run_dir], 1.0, 79, 1, lambda _text: next(replies))
            self.assertEqual(report["overall"]["assertions"], 4)
            self.assertEqual([d["assertion"] for d in report["disagreements"]], [2])
            self.assertEqual(report["disagreements"][0]["trial_id"], "case-r1")
            self.assertIn("Disagreements (1)", spotcheck.render_markdown({**report, "fraction": 1.0, "seed": 79,
                          "grader": {"provider": "OpenAI", "model": "g"}, "reference_grader": {"model": "m"}}))

    def test_by_condition_weights_by_assertions(self) -> None:
        bundles = [
            {"provider": "Anthropic", "condition": "baseline", "assertions": 10, "claude_pass_rate": 0.5, "codex_pass_rate": 0.4},
            {"provider": "Anthropic", "condition": "baseline", "assertions": 30, "claude_pass_rate": 0.9, "codex_pass_rate": 0.8},
            {"provider": "Anthropic", "condition": "with-skill", "assertions": 10, "claude_pass_rate": 1.0, "codex_pass_rate": 1.0},
        ]
        rows = {(r["provider"], r["condition"]): r for r in spotcheck.by_condition(bundles)}
        base = rows[("Anthropic", "baseline")]
        self.assertEqual(base["assertions"], 40)
        self.assertAlmostEqual(base["claude_pass_rate"], 0.8)
        self.assertAlmostEqual(base["codex_pass_rate"], 0.7)

    def test_grader_input_numbers_assertions(self) -> None:
        text = spotcheck.build_grader_input("RULES", {"prompt": "Q?", "assertions": ["a", "b"]}, "ANSWER")
        self.assertIn("1. a\n2. b", text)
        self.assertTrue(text.index("RULES") < text.index("## Question") < text.index("<answer>"))


if __name__ == "__main__":
    unittest.main()
