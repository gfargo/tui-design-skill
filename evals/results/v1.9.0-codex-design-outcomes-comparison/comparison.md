# Codex two-condition comparison (v1.9.0)

This study measures how the v1.9.0 skill changes the Codex CLI's answers with `gpt-6.1-sol` at low reasoning effort on one new eval set of eight outcome-based design cases, against a no-skill baseline that uses the same host, model, runner, and prompts. It covers Codex only. The matching Claude study is in [`../v1.9.0-claude-design-outcomes-comparison/`](../v1.9.0-claude-design-outcomes-comparison/comparison.md).

## Protocol

- **Host and model:** OpenAI Codex CLI 0.164.0-alpha.11.1 (`codex exec`), model `gpt-6.1-sol` with `model_reasoning_effort=low`. This is a newer build than the 0.160.0 used for the v1.8.0 study. The CLI exposes neither seed nor temperature, and the bundles record its system prompt as unavailable.
- **Runner:** [`scripts/runners/codex_runner.py`](../../../scripts/runners/codex_runner.py). Every trial ran in an empty temporary directory in a read-only, ephemeral sandbox, with the user's `config.toml` ignored and web search disabled. Every user-installed skill, including any installed copy of this one, was disabled through `skills.config`; a with-skill prompt names the skill directory, which the sandbox can read.
- **Skill snapshot:** `plugins/tui-design/skills/tui-design`, tree SHA-256 `164c1aefd956a6e11e4155c84769ffd130986a99b5b8809ffea1e6354f6ca570`. The skill is byte-identical to `main` at `f7a3e2a`.
- **Source commit:** every bundle in this study ran at `f7a3e2a` with a clean tree (`dirty: false` in every manifest).
- **Design:** three repetitions per case and condition, with a 1,200-second trial timeout. No trial in a committed bundle failed or timed out.
- **Grading:** blind, by `claude-opus-5-5` through [`scripts/runners/claude_grader.py`](../../../scripts/runners/claude_grader.py) with protocol `v180-direct-rubric-v1`. The grader saw the question, the numbered assertions, and the answer, never the condition, host, or model. Each assertion has a grader note in `grades.json`.
- **What the set is:** eight design-review cases whose assertions are observable outcomes of the answer, such as the nesting depth of a mockup, whether a sketch fits in 60 or 80 columns, whether a footer fits in 40, which servers a screen names, and whether seeded defects are found. The rubric was committed (`f7a3e2a`) before the first run, and the mockups' ground truth was checked by script. It is phase 2 of [#79](https://github.com/gfargo/tui-design-skill/issues/79).

| Eval set | Eval-set SHA-256 |
|---|---|
| `evals/design-outcomes-evals.json` | `370121fb52fe…` |

## Results

| Eval set | Cases | Baseline | With skill | Difference |
|---|---:|---:|---:|---:|
| `evals/design-outcomes-evals.json` | 8 | 134/156 (85.9%) | 150/156 (96.2%) | +10.3 pp |

Each set is reported on its own because the sets differ in size and difficulty.

### Outcome-based design cases

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `count-the-borders` | 12/21 (57.1%) | 20/21 (95.2%) | +38.1 pp |
| `sixty-column-sketch` | 15/18 (83.3%) | 16/18 (88.9%) | +5.6 pp |
| `partial-failure-screen` | 21/21 (100.0%) | 21/21 (100.0%) | +0.0 pp |
| `focus-without-color` | 18/18 (100.0%) | 18/18 (100.0%) | +0.0 pp |
| `footer-at-two-widths` | 20/21 (95.2%) | 21/21 (100.0%) | +4.8 pp |
| `seeded-defects-bubbletea` | 18/18 (100.0%) | 18/18 (100.0%) | +0.0 pp |
| `log-viewer-from-scratch` | 18/21 (85.7%) | 19/21 (90.5%) | +4.8 pp |
| `delete-confirmation` | 12/18 (66.7%) | 17/18 (94.4%) | +27.8 pp |
| **Aggregate** | **134/156 (85.9%)** | **150/156 (96.2%)** | **+10.3 pp** |

## Repetition variance

| Eval set | Baseline per repetition (%) | Baseline SD (pp) | With skill per repetition (%) | With-skill SD (pp) | Paired difference range |
|---|---|---:|---|---:|---|
| `design-outcomes` | 86.5 / 82.7 / 88.5 | 2.40 | 96.2 / 100.0 / 92.3 | 3.14 | +3.8 to +17.3 |

SD is the population standard deviation of the per-repetition pass rates. Every paired repetition in every set favored the with-skill condition.

## What the skill did not lift

Assertions the with-skill condition still missed, with the number of the three repetitions that missed them:

| Case | Assertion | Missed |
|---|---|---:|
| `count-the-borders` | 3. Points out that the > marker appears on all three rows, so it separates none of them from the others | 1/3 |
| `delete-confirmation` | 4. The sketch is no wider than 64 characters (80 percent of the terminal width) | 1/3 |
| `log-viewer-from-scratch` | 1. Includes at least one plain-text sketch of the screen, and no line of any sketch is wider than 80 characters | 1/3 |
| `log-viewer-from-scratch` | 5. Describes what the user sees when no log lines have arrived yet, and what they can do | 1/3 |
| `sixty-column-sketch` | 2. No line of that sketch is longer than 60 characters | 2/3 |

5 assertion rows were missed at least once; every other with-skill assertion passed in all three repetitions. The grader note for each miss is in `grades.json`.

## What the numbers support

Under this host, model, runner, prompt set, and three-repetition protocol, explicit use of the skill raised the assertion pass rate, from 85.9% to 96.2% of assertions. The largest per-case gains are `count-the-borders` (+38.1 pp), `delete-confirmation` (+27.8 pp), `sixty-column-sketch` (+5.6 pp), `log-viewer-from-scratch` (+4.8 pp), `footer-at-two-widths` (+4.8 pp). 3 of 8 cases were already at 100% in the baseline, and none scored lower with the skill.

These results don't establish a population-level effect and don't transfer to other models or hosts. They also say nothing about whether the skill activates on its own: every with-skill prompt named the skill explicitly. [#21](https://github.com/gfargo/tui-design-skill/issues/21) tracked implicit triggering, and the trigger calibration is in [`../v1.8.0-trigger-calibration/`](../v1.8.0-trigger-calibration/report.md).

## Limitations

- **Author-written rubric:** the same project wrote the skill, the prompts, and the assertions. The assertions are outcomes that should hold for any correct answer, and they were fixed before the run, but a reader should still judge whether each one is fair.
- **Ambiguous width and count assertions:** the grader spot-check found its disagreements concentrated in assertions such as "no line is wider than 64 characters" and "states that a row sits behind three borders", where a sketch with leading spaces, a backdrop, or an unusual phrasing can be read two ways. Because the rubric was committed before the run, it was not changed for this study. A later revision should say that width limits apply to the screen or dialog itself, excluding indentation, and should state how counts may be phrased.
- **Eight cases:** a small set. Per-case differences of one or two assertions are within noise, and the set samples a few kinds of design question, not all of them.
- **Not measured here:** compiled and running build output, which needs the objective checks in phase 3 of [#79](https://github.com/gfargo/tui-design-skill/issues/79).
- **Same-family grader:** Claude Opus 5.5 graded every answer, including the Codex answers. The grader never saw the condition or the host, but self-preference can't be ruled out. A Codex re-grade of a sample is in [`../v1.9.0-design-outcomes-spotcheck/`](../v1.9.0-design-outcomes-spotcheck/spotcheck.md) (see *Grader spot-check* below).
- **Small samples:** three repetitions per case; per-case differences of one or two assertions are within noise.
- **CLI build:** Codex CLI 0.164.0-alpha.11.1, the same build as the earlier v1.9.0 Codex studies.

## Grader spot-check

A deterministic 40% sample of trials (258 assertions across the four bundles of this study) was re-graded by OpenAI `gpt-6.1-sol` with each bundle's own grading prompt. The two graders agreed on 243/258 assertions (94.2%), Cohen's kappa 0.62; the Claude grader passed 92.2% and the Codex grader 91.1% of the sample. Of the 15 disagreements, 9 were a Claude pass that Codex failed and 6 the reverse. The skill's measured gain on the sample, by each grader: for Claude answers, +0.1 pp by the Claude grader and +1.7 pp by the Codex grader; for Codex answers, +15.8 pp by the Claude grader and +15.8 pp by the Codex grader. Every disagreement is listed in [`../v1.9.0-design-outcomes-spotcheck/spotcheck.md`](../v1.9.0-design-outcomes-spotcheck/spotcheck.md).

## Evidence bundles

Each directory holds the run manifest, prompts, responses, stderr, grading prompt, grades with a note for every assertion, and summary:

- [`v190-design-outcomes-codex-baseline-r3/`](v190-design-outcomes-codex-baseline-r3/) and [`v190-design-outcomes-codex-with-skill-r3/`](v190-design-outcomes-codex-with-skill-r3/)
