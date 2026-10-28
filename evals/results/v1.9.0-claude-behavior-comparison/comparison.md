# Claude two-condition comparison (v1.9.0)

This study measures how the v1.9.0 skill changes Claude Opus 5.5's answers on five older eval sets that had never been run, against a no-skill baseline that uses the same host, model, runner, and prompts. It covers Claude only. The matching Codex study is in [`../v1.9.0-codex-behavior-comparison/`](../v1.9.0-codex-behavior-comparison/comparison.md).

## Protocol

- **Host and model:** Claude Code 2.1.295 in non-interactive mode (`claude -p`), model `claude-opus-5-5` at its default effort. The CLI exposes neither seed nor temperature, and the bundles record its system prompt as unavailable.
- **Runner:** [`scripts/runners/claude_runner.py`](../../../scripts/runners/claude_runner.py). Every trial ran in an empty temporary directory with skills, slash commands, MCP servers, and user settings switched off, and with only the Read, Glob, and Grep tools. A with-skill prompt names the skill directory and that one directory is added with `--add-dir`.
- **Skill snapshot:** `plugins/tui-design/skills/tui-design`, tree SHA-256 `164c1aefd956a6e11e4155c84769ffd130986a99b5b8809ffea1e6354f6ca570`. The skill is byte-identical to `main` at `7d39c34`.
- **Source commit:** every bundle in this study ran at `7d39c34` with a clean tree (`dirty: false` in every manifest).
- **Design:** three repetitions per case and condition, with a 1,200-second trial timeout. No trial in a committed bundle failed or timed out.
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
| `evals/evals.json` | 3 | 36/39 (92.3%) | 39/39 (100.0%) | +7.7 pp |
| `evals/v160-structural-evals.json` | 3 | 35/42 (83.3%) | 40/42 (95.2%) | +11.9 pp |
| `evals/tier2-content-evals.json` | 6 | 85/90 (94.4%) | 84/90 (93.3%) | -1.1 pp |
| `evals/tier3-content-evals.json` | 4 | 51/60 (85.0%) | 60/60 (100.0%) | +15.0 pp |
| `evals/v174-correction-evals.json` | 11 | 57/111 (51.4%) | 100/111 (90.1%) | +38.7 pp |
| **All five sets** | 27 | **264/342 (77.2%)** | **323/342 (94.4%)** | **+17.3 pp** |

Each set is reported on its own because the sets differ in size and difficulty.

### Clutter and floor reviews (evals.json)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `cluttered-ci-dashboard-review` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| `responsive-miller-columns` | 15/15 (100.0%) | 15/15 (100.0%) | +0.0 pp |
| `open-ended-k8s-tui-review` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| **Aggregate** | **36/39 (92.3%)** | **39/39 (100.0%)** | **+7.7 pp** |

### Structural forward tests (v160)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `bubble-tea-cleanup-after-slimming` | 11/12 (91.7%) | 12/12 (100.0%) | +8.3 pp |
| `kubernetes-browser-clutter-and-floor` | 14/15 (93.3%) | 15/15 (100.0%) | +6.7 pp |
| `branch-picker-output-contract` | 10/15 (66.7%) | 13/15 (86.7%) | +20.0 pp |
| **Aggregate** | **35/42 (83.3%)** | **40/42 (95.2%)** | **+11.9 pp** |

### Tier-2 content (testing, debugging, inline mode, OSC)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `go-testing-ci` | 15/15 (100.0%) | 15/15 (100.0%) | +0.0 pp |
| `textual-testing-form` | 15/15 (100.0%) | 15/15 (100.0%) | +0.0 pp |
| `ratatui-debug-regression` | 15/15 (100.0%) | 15/15 (100.0%) | +0.0 pp |
| `ink-debug-workflow` | 14/15 (93.3%) | 14/15 (93.3%) | +0.0 pp |
| `inline-vs-altscreen-picker` | 15/15 (100.0%) | 14/15 (93.3%) | -6.7 pp |
| `osc-clipboard-hyperlinks-ssh` | 11/15 (73.3%) | 11/15 (73.3%) | +0.0 pp |
| **Aggregate** | **85/90 (94.4%)** | **84/90 (93.3%)** | **-1.1 pp** |

### Tier-3 content (shell integration, forms and auth, Nerd Fonts, profiling)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `shell-integration-cd-on-exit` | 15/15 (100.0%) | 15/15 (100.0%) | +0.0 pp |
| `forms-first-run-apikey` | 14/15 (93.3%) | 15/15 (100.0%) | +6.7 pp |
| `nerdfont-and-timeout-ux` | 13/15 (86.7%) | 15/15 (100.0%) | +13.3 pp |
| `profiling-textual-and-ink` | 9/15 (60.0%) | 15/15 (100.0%) | +40.0 pp |
| **Aggregate** | **51/60 (85.0%)** | **60/60 (100.0%)** | **+15.0 pp** |

### v1.7.4 corrections

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `huh-v2-embedding` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| `lipgloss-v2-printing` | 9/9 (100.0%) | 9/9 (100.0%) | +0.0 pp |
| `ratatui-textarea-crate` | 0/9 (0.0%) | 6/9 (66.7%) | +66.7 pp |
| `ratatui-select-reader-ends` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `ratatui-ctrl-c-raw-mode` | 9/9 (100.0%) | 9/9 (100.0%) | +0.0 pp |
| `ink8-new-project` | 3/12 (25.0%) | 12/12 (100.0%) | +75.0 pp |
| `cjs-require-esm` | 9/9 (100.0%) | 8/9 (88.9%) | -11.1 pp |
| `typer-vendored-click` | 0/9 (0.0%) | 9/9 (100.0%) | +100.0 pp |
| `ai-chat-rendering-tradeoff` | 0/12 (0.0%) | 5/12 (41.7%) | +41.7 pp |
| `gocui-new-app` | 3/9 (33.3%) | 9/9 (100.0%) | +66.7 pp |
| `textual-snapshot-pytest9` | 3/9 (33.3%) | 9/9 (100.0%) | +66.7 pp |
| **Aggregate** | **57/111 (51.4%)** | **100/111 (90.1%)** | **+38.7 pp** |

## Repetition variance

| Eval set | Baseline per repetition (%) | Baseline SD (pp) | With skill per repetition (%) | With-skill SD (pp) | Paired difference range |
|---|---|---:|---|---:|---|
| `design-review` | 92.3 / 92.3 / 92.3 | 0.00 | 100.0 / 100.0 / 100.0 | 0.00 | +7.7 to +7.7 |
| `structural` | 85.7 / 78.6 / 85.7 | 3.37 | 92.9 / 92.9 / 100.0 | 3.37 | +7.1 to +14.3 |
| `tier2` | 96.7 / 93.3 / 93.3 | 1.57 | 93.3 / 93.3 / 93.3 | 0.00 | -3.3 to +0.0 |
| `tier3` | 85.0 / 85.0 / 85.0 | 0.00 | 100.0 / 100.0 / 100.0 | 0.00 | +15.0 to +15.0 |
| `v174` | 51.4 / 51.4 / 51.4 | 0.00 | 97.3 / 83.8 / 89.2 | 5.55 | +32.4 to +45.9 |

SD is the population standard deviation of the per-repetition pass rates. Not every paired repetition favored the with-skill condition.

## What the skill did not lift

Assertions the with-skill condition still missed, with the number of the three repetitions that missed them:

| Case | Assertion | Missed |
|---|---|---:|
| `branch-picker-output-contract` | 4. Keeps git/subprocess work outside Update and returns results through a tea.Cmd or message | 2/3 |
| `ink-debug-workflow` | 2. Recommends React DevTools attachment for Ink (DEV=true) to inspect the component tree and state | 1/3 |
| `inline-vs-altscreen-picker` | 1. Recommends inline (non-alt-screen) rendering for this bounded summon-choose-exit picker, with the explicit reasoning that the alt screen would erase the context the user wants to preserve | 1/3 |
| `osc-clipboard-hyperlinks-ssh` | 4. Notes real-world limits honestly: emulator support varies, OSC 52 size caps, and a fallback (shell out to pbcopy/xclip/wl-copy when local) is still worth having | 2/3 |
| `osc-clipboard-hyperlinks-ssh` | 5. Warns that clipboard READ via OSC 52 is a security-sensitive capability most terminals disable (write-only is the safe design) | 2/3 |
| `ai-chat-rendering-tradeoff` | 1. Corrects the premise: Claude Code's fullscreen renderer uses the alternate screen and renders only visible messages, and GitHub Copilot CLI uses the alternate screen, while Gemini CLI stays inline | 2/3 |
| `ai-chat-rendering-tradeoff` | 2. Explains that inline rendering keeps the terminal's scrollback, search, and copy, but its cost grows with the transcript | 2/3 |
| `ai-chat-rendering-tradeoff` | 3. Explains that an alternate-screen renderer keeps memory flat and avoids flicker but must rebuild search, copy, and export to scrollback | 2/3 |
| `ai-chat-rendering-tradeoff` | 4. Recommends keeping an inline or plain fallback for screen readers or users who prefer scrollback | 1/3 |
| `cjs-require-esm` | 1. Says Node 22.12 and later (and 20.19) can require() synchronous ES modules, so ESM-only packages such as chalk and commander no longer force old pins | 1/3 |
| `ratatui-textarea-crate` | 3. Warns against pulling in a second crossterm version, or imports crossterm through ratatui::crossterm | 3/3 |

11 assertion rows were missed at least once; every other with-skill assertion passed in all three repetitions. The grader note for each miss is in `grades.json`.

## What the numbers support

Under this host, model, runner, prompt set, and three-repetition protocol, explicit use of the skill raised the assertion pass rate on 4 of 5 sets (`tier2` -1.1 pp), moving the set pass rates from 51.4–94.4% to 90.1–100.0%. The largest per-case gains are `typer-vendored-click` (+100.0 pp), `ink8-new-project` (+75.0 pp), `textual-snapshot-pytest9` (+66.7 pp), `gocui-new-app` (+66.7 pp), `ratatui-textarea-crate` (+66.7 pp). 11 of 27 cases were already at 100% in the baseline; 2 cases scored lower with the skill: `inline-vs-altscreen-picker` (15/15 to 14/15); `cjs-require-esm` (9/9 to 8/9).

These results don't establish a population-level effect and don't transfer to other models or hosts. They also say nothing about whether the skill activates on its own: every with-skill prompt named the skill explicitly. [#21](https://github.com/gfargo/tui-design-skill/issues/21) tracked implicit triggering, and the trigger calibration is in [`../v1.8.0-trigger-calibration/`](../v1.8.0-trigger-calibration/report.md).

## Limitations

- **Saturation:** 9 of 27 cases scored 100% in both conditions, so they cannot show an effect. Several rubrics were also written from the skill's own text, so a high with-skill score can mean the answer repeated what it read. On the clutter and floor reviews the baseline already scored 92.3% and on the structural tests 83.3%; the set of corrections to facts newer than the model (`v174`) is where the baseline is lowest (51.4%).
- **Not measured here:** compiled and running build output, and design quality beyond what the rubrics check. Phases 2 and 3 of [#79](https://github.com/gfargo/tui-design-skill/issues/79) (outcome-based design cases and objective build checks) address those.
- **Same-family grader:** Claude Opus 5.5 graded every answer, including its own. The grader never saw the condition or the host, but self-preference can't be ruled out. A Codex re-grade of a sample is in [`../v1.9.0-grader-spotcheck/`](../v1.9.0-grader-spotcheck/spotcheck.md) (see *Grader spot-check* below).
- **Small samples:** three repetitions per case; per-case differences of one or two assertions are within noise.

## Grader spot-check

A deterministic 15% sample of trials (612 assertions across the bundles of this study and the earlier v1.9.0 study) was re-graded by OpenAI `gpt-6.1-sol` with each bundle's own grading prompt. The two graders agreed on 576/612 assertions (94.1%), Cohen's kappa 0.83; the Claude grader passed 80.7% and the Codex grader 75.8% of the sample. Codex was the stricter grader: 33 of the 36 disagreements were a Claude pass that Codex failed. The skill's measured gain holds under both graders: for Claude answers, +26.7 pp by the Claude grader and +32.7 pp by the Codex grader; for Codex answers, +33.5 pp by the Claude grader and +30.3 pp by the Codex grader. Every disagreement is listed in [`../v1.9.0-grader-spotcheck/spotcheck.md`](../v1.9.0-grader-spotcheck/spotcheck.md).

## Evidence bundles

Each directory holds the run manifest, prompts, responses, stderr, grading prompt, grades with a note for every assertion, and summary:

- [`v190-design-review-claude-baseline-r3/`](v190-design-review-claude-baseline-r3/) and [`v190-design-review-claude-with-skill-r3/`](v190-design-review-claude-with-skill-r3/)
- [`v190-structural-claude-baseline-r3/`](v190-structural-claude-baseline-r3/) and [`v190-structural-claude-with-skill-r3/`](v190-structural-claude-with-skill-r3/)
- [`v190-tier2-claude-baseline-r3/`](v190-tier2-claude-baseline-r3/) and [`v190-tier2-claude-with-skill-r3/`](v190-tier2-claude-with-skill-r3/)
- [`v190-tier3-claude-baseline-r3/`](v190-tier3-claude-baseline-r3/) and [`v190-tier3-claude-with-skill-r3/`](v190-tier3-claude-with-skill-r3/)
- [`v190-v174-claude-baseline-r3/`](v190-v174-claude-baseline-r3/) and [`v190-v174-claude-with-skill-r3/`](v190-v174-claude-with-skill-r3/)
