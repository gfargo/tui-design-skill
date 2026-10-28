#!/usr/bin/env python3
"""Spot-check the Claude grader with a second, non-Claude grader.

Every recorded bundle is graded blind by Claude. This script re-grades a
deterministic sample of trials with the Codex CLI (through the isolated
scripts/runners/codex_runner.py), using each bundle's own preserved grading
prompt, and reports how often the two graders agree on each assertion. It
writes a standalone JSON report and a Markdown summary; it does not touch the
bundles or their grades.

Usage:
  python3 scripts/grader_spotcheck.py --runs evals/results/v1.9.0-claude-comparison/*/ \\
    --fraction 0.15 --seed 79 --jobs 3 --runner-version "codex-cli 0.164.0" \\
    --output spotcheck/spotcheck.json
Set CODEX_BIN to choose the Codex binary (the runner reads it).
"""

import argparse
import hashlib
import json
import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts/runners"))
from claude_grader import parse_results  # noqa: E402

REPORT_SCHEMA = "tui-design grader spot-check v1"


def sample_trials(run_id, trials, fraction, seed):
    """Deterministically choose ceil(fraction * n) trials (at least one) from one bundle."""
    count = max(1, math.ceil(len(trials) * fraction))
    ranked = sorted(trials, key=lambda t: hashlib.sha256(f"{seed}:{run_id}:{t['trial_id']}".encode()).hexdigest())
    chosen = {t["trial_id"] for t in ranked[:count]}
    return [t for t in trials if t["trial_id"] in chosen]


def cohens_kappa(pairs):
    """Cohen's kappa for two binary raters; None when chance agreement is 1 (no variation)."""
    total = len(pairs)
    if total == 0:
        return None
    observed = sum(a == b for a, b in pairs) / total
    pa = sum(a for a, _ in pairs) / total
    pb = sum(b for _, b in pairs) / total
    expected = pa * pb + (1 - pa) * (1 - pb)
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)


def summarize(pairs):
    total = len(pairs)
    return {
        "assertions": total,
        "agree": sum(a == b for a, b in pairs),
        "agreement": (sum(a == b for a, b in pairs) / total) if total else None,
        "kappa": cohens_kappa(pairs),
        "claude_pass_rate": (sum(a for a, _ in pairs) / total) if total else None,
        "codex_pass_rate": (sum(b for _, b in pairs) / total) if total else None,
    }


def by_condition(bundles):
    """Weighted pass rates of both graders, grouped by the answering provider and condition."""
    groups = {}
    for b in bundles:
        g = groups.setdefault((b["provider"], b["condition"]), {"assertions": 0, "claude": 0.0, "codex": 0.0})
        g["assertions"] += b["assertions"]
        g["claude"] += b["claude_pass_rate"] * b["assertions"]
        g["codex"] += b["codex_pass_rate"] * b["assertions"]
    return [{"provider": p, "condition": c, "assertions": g["assertions"],
             "claude_pass_rate": g["claude"] / g["assertions"], "codex_pass_rate": g["codex"] / g["assertions"]}
            for (p, c), g in sorted(groups.items())]


def build_grader_input(instructions, case, response):
    numbered = "\n".join(f"{i + 1}. {text}" for i, text in enumerate(case["assertions"]))
    return (
        f"{instructions}\n\n## Question\n\n{case['prompt']}\n\n## Assertions\n\n{numbered}\n\n"
        f"## Answer to grade\n\n<answer>\n{response}\n</answer>\n"
    )


def codex_grade(runner_args, grader_input):
    """Run one grading prompt through the isolated Codex runner and return its reply."""
    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/runners/codex_runner.py"), *runner_args],
        input=grader_input, text=True, capture_output=True, cwd=REPO_ROOT,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"codex grader exited {completed.returncode}: {completed.stderr[-400:]}")
    return completed.stdout


def run_spotcheck(run_dirs, fraction, seed, jobs, grade_fn):
    work = []
    for run_dir in run_dirs:
        manifest = json.loads((run_dir / "run.json").read_text())
        claude = json.loads((run_dir / "grades.json").read_text())
        claude_by_trial = {t["trial_id"]: t["assertions"] for t in claude["trials"]}
        eval_set = json.loads((REPO_ROOT / manifest["eval_set"]).read_text())
        cases = {str(c["id"]): c for c in eval_set["evals"]}
        cases.update({c["name"]: c for c in eval_set["evals"]})
        instructions = (run_dir / "grading-prompt.md").read_text()
        for trial in sample_trials(manifest["run_id"], manifest["trials"], fraction, seed):
            work.append((manifest, run_dir, instructions, cases[str(trial["case_id"])], trial, claude_by_trial[trial["trial_id"]]))

    def grade(item):
        manifest, run_dir, instructions, case, trial, claude_assertions = item
        response = (run_dir / trial["response_file"]).read_text()
        last = None
        for _ in range(3):
            try:
                results = parse_results(grade_fn(build_grader_input(instructions, case, response)), len(case["assertions"]))
                break
            except (RuntimeError, ValueError) as error:
                last = error
        else:
            raise SystemExit(f"{trial['trial_id']}: unusable grader reply after 3 attempts: {last}")
        return manifest, case, trial, claude_assertions, results

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        graded = list(pool.map(grade, work))

    bundles, disagreements, all_pairs = {}, [], []
    for manifest, case, trial, claude_assertions, results in graded:
        bundle = bundles.setdefault(manifest["run_id"], {"run_id": manifest["run_id"], "condition": manifest["condition"],
                                                          "provider": manifest["provider"], "trials": 0, "pairs": []})
        bundle["trials"] += 1
        for index, (passed, note) in enumerate(results):
            claude = claude_assertions[index]
            pair = (bool(claude["passed"]), bool(passed))
            bundle["pairs"].append(pair)
            all_pairs.append(pair)
            if pair[0] != pair[1]:
                disagreements.append({
                    "run_id": manifest["run_id"], "trial_id": trial["trial_id"], "assertion": index + 1,
                    "text": case["assertions"][index],
                    "claude": {"passed": pair[0], "note": claude["notes"]}, "codex": {"passed": pair[1], "note": note},
                })
    out_bundles = []
    for bundle in bundles.values():
        pairs = bundle.pop("pairs")
        out_bundles.append({**bundle, **summarize(pairs)})
    out_bundles = sorted(out_bundles, key=lambda b: b["run_id"])
    return {"bundles": out_bundles, "overall": summarize(all_pairs), "by_condition": by_condition(out_bundles), "disagreements": disagreements}


def render_markdown(report):
    o = report["overall"]
    fmt = lambda x: "n/a" if x is None else f"{x:.3f}"
    lines = [
        "# Grader spot-check", "",
        f"A deterministic {report['fraction']:.0%} sample of trials (seed {report['seed']}) from {len(report['bundles'])} bundles, "
        f"re-graded by {report['grader']['provider']} `{report['grader']['model']}` with each bundle's own grading prompt, "
        f"compared with the original {report['reference_grader']['model']} grades.", "",
        f"- **Assertions compared:** {o['assertions']}",
    ]
    if o["assertions"]:
        lines += [
            f"- **Agreement:** {o['agree']}/{o['assertions']} ({100 * o['agreement']:.1f}%)",
            f"- **Cohen's kappa:** {fmt(o['kappa'])}",
            f"- **Pass rate:** Claude grader {100 * o['claude_pass_rate']:.1f}%, Codex grader {100 * o['codex_pass_rate']:.1f}%",
        ]
    conditions = report.get("by_condition") or by_condition(report["bundles"])
    lines += ["", "## Pass rate by answering provider and condition", "",
              "| Answers from | Condition | Assertions | Claude grader | Codex grader |", "|---|---|---:|---:|---:|"]
    for c in conditions:
        lines.append(f"| {c['provider']} | {c['condition']} | {c['assertions']} | {100 * c['claude_pass_rate']:.1f}% | {100 * c['codex_pass_rate']:.1f}% |")
    lines += ["", "## Per bundle", "", "| Bundle | Trials | Assertions | Agreement | Kappa |", "|---|---:|---:|---:|---:|"]
    for b in report["bundles"]:
        lines.append(f"| `{b['run_id']}` | {b['trials']} | {b['assertions']} | {100 * b['agreement']:.1f}% | {fmt(b['kappa'])} |")
    lines += ["", f"## Disagreements ({len(report['disagreements'])})", ""]
    for d in report["disagreements"]:
        lines.append(f"- `{d['trial_id']}` in `{d['run_id']}`, assertion {d['assertion']}: Claude **{'pass' if d['claude']['passed'] else 'fail'}**, Codex **{'pass' if d['codex']['passed'] else 'fail'}**. {d['text']}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", nargs="+", required=True, type=Path, help="bundle directories (each with run.json and grades.json)")
    parser.add_argument("--fraction", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=79)
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--model", default="gpt-6.1-sol")
    parser.add_argument("--effort", default="low")
    parser.add_argument("--runner-version", required=True, help="exact Codex CLI version string, recorded in the report")
    parser.add_argument("--output", required=True, type=Path, help="report JSON path; a .md summary is written beside it")
    args = parser.parse_args()
    run_dirs = [p.resolve() for p in args.runs if (p / "run.json").is_file()]
    if not run_dirs:
        raise SystemExit("no bundle directories with run.json")
    reference = json.loads((run_dirs[0] / "grades.json").read_text())["grader"]
    runner_args = ["--model", args.model, "--effort", args.effort]
    report = run_spotcheck(run_dirs, args.fraction, args.seed, args.jobs, lambda text: codex_grade(runner_args, text))
    report = {
        "schema": REPORT_SCHEMA, "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "fraction": args.fraction, "seed": args.seed,
        "grader": {"provider": "OpenAI", "model": args.model, "effort": args.effort, "runner_version": args.runner_version},
        "reference_grader": {"provider": reference["provider"], "model": reference["model"], "prompt_version": reference["prompt_version"]},
        **report,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    args.output.with_suffix(".md").write_text(render_markdown(report))
    print(args.output)


if __name__ == "__main__":
    main()
