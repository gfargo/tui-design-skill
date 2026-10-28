# Codex two-condition comparison (v1.9.0)

This study measures how the v1.9.0 skill changes the Codex CLI's answers with `gpt-6.1-sol` at low reasoning effort on five older eval sets that had never been run, against a no-skill baseline that uses the same host, model, runner, and prompts. It covers Codex only. The matching Claude study is in [`../v1.9.0-claude-behavior-comparison/`](../v1.9.0-claude-behavior-comparison/comparison.md).

## Protocol

- **Host and model:** OpenAI Codex CLI 0.164.0-alpha.11.1 (`codex exec`), model `gpt-6.1-sol` with `model_reasoning_effort=low`. This is a newer build than the 0.160.0 used for the v1.8.0 study. The CLI exposes neither seed nor temperature, and the bundles record its system prompt as unavailable.
- **Runner:** [`scripts/runners/codex_runner.py`](../../../scripts/runners/codex_runner.py). Every trial ran in an empty temporary directory in a read-only, ephemeral sandbox, with the user's `config.toml` ignored and web search disabled. Every user-installed skill, including any installed copy of this one, was disabled through `skills.config`; a with-skill prompt names the skill directory, which the sandbox can read.
- **Skill snapshot:** `plugins/tui-design/skills/tui-design`, tree SHA-256 `164c1aefd956a6e11e4155c84769ffd130986a99b5b8809ffea1e6354f6ca570`. The skill is byte-identical to `main` at `7d39c34`.
- **Source commit:** every bundle in this study ran at `7d39c34` with a clean tree (`dirty: false` in every manifest).
- **Design:** three repetitions per case and condition, with a 1,200-second trial timeout. No trial in a committed bundle failed or timed out. The Codex account hit its usage limit twice: all ten jobs failed on the first attempt, and one more (design-review with-skill) was cut off partway through the final attempt. Every affected bundle was discarded and rerun in full at the same commit after the limit reset, so no failed trial is committed.
- **Grading:** blind, by `claude-opus-5-5` through [`scripts/runners/claude_grader.py`](../../../scripts/runners/claude_grader.py) with protocol `v180-direct-rubric-v1`. The grader saw the question, the numbered assertions, and the answer, never the condition, host, or model. Each assertion has a grader note in `grades.json`.
- **What the sets are:** the design-review clutter and floor cases (`evals.json`, `v160-structural-evals.json`), the tier-2 and tier-3 content sets, and the v1.7.4 corrections. They were written for earlier releases and had no recorded run before this study ([#79](https://github.com/gfargo/tui-design-skill/issues/79)). Build tasks (`build-evals.json`) are not included; they need objective checks that this study does not have.

| Eval set | Eval-set SHA-256 |
|---|---|
| `evals/evals.json` | `85b7e379fb6d…` |
| `evals/v160-structural-evals.json` | `98283b25dece…` |
| `evals/tier2-content-evals.json` | `358ecc415809…` |
| `evals/tier3-content-evals.json` | `1609e5076ad8…` |
| `evals/v174-correction-evals.json` | `3932ca512827…` |

## Results

| Eval set | Cases | Baseline | With skill | Difference |
|---|---:|---:|---:|---:|
| `evals/evals.json` | 3 | 33/39 (84.6%) | 39/39 (100.0%) | +15.4 pp |
| `evals/v160-structural-evals.json` | 3 | 28/42 (66.7%) | 42/42 (100.0%) | +33.3 pp |
| `evals/tier2-content-evals.json` | 6 | 60/90 (66.7%) | 74/90 (82.2%) | +15.6 pp |
| `evals/tier3-content-evals.json` | 4 | 42/60 (70.0%) | 55/60 (91.7%) | +21.7 pp |
| `evals/v174-correction-evals.json` | 11 | 54/111 (48.6%) | 90/111 (81.1%) | +32.4 pp |
| **All five sets** | 27 | **217/342 (63.5%)** | **300/342 (87.7%)** | **+24.3 pp** |

Each set is reported on its own because the sets differ in size and difficulty.

### Clutter and floor reviews (evals.json)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `cluttered-ci-dashboard-review` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| `responsive-miller-columns` | 12/15 (80.0%) | 15/15 (100.0%) | +20.0 pp |
| `open-ended-k8s-tui-review` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| **Aggregate** | **33/39 (84.6%)** | **39/39 (100.0%)** | **+15.4 pp** |

### Structural forward tests (v160)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `bubble-tea-cleanup-after-slimming` | 11/12 (91.7%) | 12/12 (100.0%) | +8.3 pp |
| `kubernetes-browser-clutter-and-floor` | 10/15 (66.7%) | 15/15 (100.0%) | +33.3 pp |
| `branch-picker-output-contract` | 7/15 (46.7%) | 15/15 (100.0%) | +53.3 pp |
| **Aggregate** | **28/42 (66.7%)** | **42/42 (100.0%)** | **+33.3 pp** |

### Tier-2 content (testing, debugging, inline mode, OSC)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `go-testing-ci` | 7/15 (46.7%) | 12/15 (80.0%) | +33.3 pp |
| `textual-testing-form` | 12/15 (80.0%) | 12/15 (80.0%) | +0.0 pp |
| `ratatui-debug-regression` | 15/15 (100.0%) | 15/15 (100.0%) | +0.0 pp |
| `ink-debug-workflow` | 11/15 (73.3%) | 15/15 (100.0%) | +26.7 pp |
| `inline-vs-altscreen-picker` | 8/15 (53.3%) | 10/15 (66.7%) | +13.3 pp |
| `osc-clipboard-hyperlinks-ssh` | 7/15 (46.7%) | 10/15 (66.7%) | +20.0 pp |
| **Aggregate** | **60/90 (66.7%)** | **74/90 (82.2%)** | **+15.6 pp** |

### Tier-3 content (shell integration, forms and auth, Nerd Fonts, profiling)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `shell-integration-cd-on-exit` | 10/15 (66.7%) | 14/15 (93.3%) | +26.7 pp |
| `forms-first-run-apikey` | 10/15 (66.7%) | 14/15 (93.3%) | +26.7 pp |
| `nerdfont-and-timeout-ux` | 12/15 (80.0%) | 12/15 (80.0%) | +0.0 pp |
| `profiling-textual-and-ink` | 10/15 (66.7%) | 15/15 (100.0%) | +33.3 pp |
| **Aggregate** | **42/60 (70.0%)** | **55/60 (91.7%)** | **+21.7 pp** |

### v1.7.4 corrections

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `huh-v2-embedding` | 6/12 (50.0%) | 12/12 (100.0%) | +50.0 pp |
| `lipgloss-v2-printing` | 9/9 (100.0%) | 9/9 (100.0%) | +0.0 pp |
| `ratatui-textarea-crate` | 1/9 (11.1%) | 6/9 (66.7%) | +55.6 pp |
| `ratatui-select-reader-ends` | 6/12 (50.0%) | 10/12 (83.3%) | +33.3 pp |
| `ratatui-ctrl-c-raw-mode` | 9/9 (100.0%) | 9/9 (100.0%) | +0.0 pp |
| `ink8-new-project` | 7/12 (58.3%) | 9/12 (75.0%) | +16.7 pp |
| `cjs-require-esm` | 8/9 (88.9%) | 9/9 (100.0%) | +11.1 pp |
| `typer-vendored-click` | 0/9 (0.0%) | 9/9 (100.0%) | +100.0 pp |
| `ai-chat-rendering-tradeoff` | 0/12 (0.0%) | 2/12 (16.7%) | +16.7 pp |
| `gocui-new-app` | 4/9 (44.4%) | 6/9 (66.7%) | +22.2 pp |
| `textual-snapshot-pytest9` | 4/9 (44.4%) | 9/9 (100.0%) | +55.6 pp |
| **Aggregate** | **54/111 (48.6%)** | **90/111 (81.1%)** | **+32.4 pp** |

## Repetition variance

| Eval set | Baseline per repetition (%) | Baseline SD (pp) | With skill per repetition (%) | With-skill SD (pp) | Paired difference range |
|---|---|---:|---|---:|---|
| `design-review` | 84.6 / 84.6 / 84.6 | 0.00 | 100.0 / 100.0 / 100.0 | 0.00 | +15.4 to +15.4 |
| `structural` | 71.4 / 71.4 / 57.1 | 6.73 | 100.0 / 100.0 / 100.0 | 0.00 | +28.6 to +42.9 |
| `tier2` | 63.3 / 70.0 / 66.7 | 2.72 | 80.0 / 83.3 / 83.3 | 1.57 | +13.3 to +16.7 |
| `tier3` | 70.0 / 65.0 / 75.0 | 4.08 | 85.0 / 95.0 / 95.0 | 4.71 | +15.0 to +30.0 |
| `v174` | 51.4 / 45.9 / 48.6 | 2.21 | 81.1 / 81.1 / 81.1 | 0.00 | +29.7 to +35.1 |

SD is the population standard deviation of the per-repetition pass rates. Every paired repetition in every set favored the with-skill condition.

## What the skill did not lift

Assertions the with-skill condition still missed, with the number of the three repetitions that missed them:

| Case | Assertion | Missed |
|---|---|---:|
| `go-testing-ci` | 2. Shows or describes the golden-file / output-assertion workflow for frames (and how to update goldens) | 3/3 |
| `textual-testing-form` | 4. Mentions pytest-textual-snapshot / snap_compare for visual regression as a complementary layer | 3/3 |
| `inline-vs-altscreen-picker` | 1. Recommends inline (non-alt-screen) rendering for this bounded summon-choose-exit picker, with the explicit reasoning that the alt screen would erase the context the user wants to preserve | 1/3 |
| `inline-vs-altscreen-picker` | 2. Explains the mechanics in current Bubble Tea (v2: a View without AltScreen set / v1: omit tea.WithAltScreen) — no stale or invented API | 2/3 |
| `inline-vs-altscreen-picker` | 4. Mentions the fzf --height pattern (bounded inline viewport) as the model for this class of tool | 2/3 |
| `osc-clipboard-hyperlinks-ssh` | 4. Notes real-world limits honestly: emulator support varies, OSC 52 size caps, and a fallback (shell out to pbcopy/xclip/wl-copy when local) is still worth having | 2/3 |
| `osc-clipboard-hyperlinks-ssh` | 5. Warns that clipboard READ via OSC 52 is a security-sensitive capability most terminals disable (write-only is the safe design) | 3/3 |
| `shell-integration-cd-on-exit` | 4. Recommends documenting the wrapper function for the user to add to their rc file themselves, not silently auto-installing it | 1/3 |
| `forms-first-run-apikey` | 1. Recommends checking isatty on both stdin and stdout before prompting, with a non-interactive fallback (env var short-circuits the flow) for CI/scripted use | 1/3 |
| `nerdfont-and-timeout-ux` | 2. Recommends an opt-in config/flag pattern citing a real precedent (lazygit's nerdFontsVersion, eza's --icons, or similar) rather than proposing a detection scheme | 3/3 |
| `ai-chat-rendering-tradeoff` | 1. Corrects the premise: Claude Code's fullscreen renderer uses the alternate screen and renders only visible messages, and GitHub Copilot CLI uses the alternate screen, while Gemini CLI stays inline | 3/3 |
| `ai-chat-rendering-tradeoff` | 2. Explains that inline rendering keeps the terminal's scrollback, search, and copy, but its cost grows with the transcript | 3/3 |
| `ai-chat-rendering-tradeoff` | 3. Explains that an alternate-screen renderer keeps memory flat and avoids flicker but must rebuild search, copy, and export to scrollback | 3/3 |
| `ai-chat-rendering-tradeoff` | 4. Recommends keeping an inline or plain fallback for screen readers or users who prefer scrollback | 1/3 |
| `gocui-new-app` | 1. Says lazygit copied its gocui fork into its own repository (pkg/gocui) on tcell v3, so there is no maintained upstream gocui to depend on | 3/3 |
| `ink8-new-project` | 4. Mentions at least one other Ink 8 breaking change, such as number-only minWidth and maxWidth or useInput dropping unrecognized terminal sequences | 3/3 |
| `ratatui-select-reader-ends` | 2. Notes the user cannot quit because Ctrl+C arrives as a key event in raw mode, not as SIGINT | 2/3 |
| `ratatui-textarea-crate` | 3. Warns against pulling in a second crossterm version, or imports crossterm through ratatui::crossterm | 3/3 |

18 assertion rows were missed at least once; every other with-skill assertion passed in all three repetitions. The grader note for each miss is in `grades.json`.

## What the numbers support

Under this host, model, runner, prompt set, and three-repetition protocol, explicit use of the skill raised the assertion pass rate on every set, moving the set pass rates from 48.6–84.6% to 81.1–100.0%. The largest per-case gains are `typer-vendored-click` (+100.0 pp), `textual-snapshot-pytest9` (+55.6 pp), `ratatui-textarea-crate` (+55.6 pp), `branch-picker-output-contract` (+53.3 pp), `huh-v2-embedding` (+50.0 pp). 4 of 27 cases were already at 100% in the baseline, and none scored lower with the skill.

These results don't establish a population-level effect and don't transfer to other models or hosts. They also say nothing about whether the skill activates on its own: every with-skill prompt named the skill explicitly. [#21](https://github.com/gfargo/tui-design-skill/issues/21) tracked implicit triggering, and the trigger calibration is in [`../v1.8.0-trigger-calibration/`](../v1.8.0-trigger-calibration/report.md).

## Limitations

- **Saturation:** 4 of 27 cases scored 100% in both conditions, so they cannot show an effect. Several rubrics were also written from the skill's own text, so a high with-skill score can mean the answer repeated what it read. On the clutter and floor reviews the baseline already scored 84.6% and on the structural tests 66.7%; the set of corrections to facts newer than the model (`v174`) is where the baseline is lowest (48.6%).
- **Not measured here:** compiled and running build output, and design quality beyond what the rubrics check. Phases 2 and 3 of [#79](https://github.com/gfargo/tui-design-skill/issues/79) (outcome-based design cases and objective build checks) address those.
- **Same-family grader:** Claude Opus 5.5 graded every answer, including the Codex answers. The grader never saw the condition or the host, but self-preference can't be ruled out. A Codex re-grade of a sample is in [`../v1.9.0-grader-spotcheck/`](../v1.9.0-grader-spotcheck/spotcheck.md) (see *Grader spot-check* below).
- **Small samples:** three repetitions per case; per-case differences of one or two assertions are within noise.
- **CLI build:** this study used Codex CLI 0.164.0-alpha.11.1; the v1.8.0 Codex study used 0.160.0, so the two Codex studies are not a controlled comparison of the skill versions.
- **No earlier Codex number:** these sets had not been run on any Codex build before, so there is nothing to compare this study with.

## Grader spot-check

A deterministic 15% sample of trials (612 assertions across the bundles of this study and the earlier v1.9.0 study) was re-graded by OpenAI `gpt-6.1-sol` with each bundle's own grading prompt. The two graders agreed on 576/612 assertions (94.1%), Cohen's kappa 0.83; the Claude grader passed 80.7% and the Codex grader 75.8% of the sample. Codex was the stricter grader: 33 of the 36 disagreements were a Claude pass that Codex failed. The skill's measured gain holds under both graders: for Claude answers, +26.7 pp by the Claude grader and +32.7 pp by the Codex grader; for Codex answers, +33.5 pp by the Claude grader and +30.3 pp by the Codex grader. Every disagreement is listed in [`../v1.9.0-grader-spotcheck/spotcheck.md`](../v1.9.0-grader-spotcheck/spotcheck.md).

## Evidence bundles

Each directory holds the run manifest, prompts, responses, stderr, grading prompt, grades with a note for every assertion, and summary:

- [`v190-design-review-codex-baseline-r3/`](v190-design-review-codex-baseline-r3/) and [`v190-design-review-codex-with-skill-r3/`](v190-design-review-codex-with-skill-r3/)
- [`v190-structural-codex-baseline-r3/`](v190-structural-codex-baseline-r3/) and [`v190-structural-codex-with-skill-r3/`](v190-structural-codex-with-skill-r3/)
- [`v190-tier2-codex-baseline-r3/`](v190-tier2-codex-baseline-r3/) and [`v190-tier2-codex-with-skill-r3/`](v190-tier2-codex-with-skill-r3/)
- [`v190-tier3-codex-baseline-r3/`](v190-tier3-codex-baseline-r3/) and [`v190-tier3-codex-with-skill-r3/`](v190-tier3-codex-with-skill-r3/)
- [`v190-v174-codex-baseline-r3/`](v190-v174-codex-baseline-r3/) and [`v190-v174-codex-with-skill-r3/`](v190-v174-codex-with-skill-r3/)
