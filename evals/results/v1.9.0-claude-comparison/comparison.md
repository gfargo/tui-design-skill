# Claude two-condition comparison (v1.9.0)

This study measures how the v1.9.0 skill changes Claude Opus 5.5's answers on five new eval sets, against a no-skill baseline that uses the same host, model, runner, and prompts. It covers Claude only. The matching Codex study is in [`../v1.9.0-codex-comparison/`](../v1.9.0-codex-comparison/comparison.md).

## Protocol

- **Host and model:** Claude Code 2.1.295 in non-interactive mode (`claude -p`), model `claude-opus-5-5` at its default effort. The CLI exposes neither seed nor temperature, and the bundles record its system prompt as unavailable.
- **Runner:** [`scripts/runners/claude_runner.py`](../../../scripts/runners/claude_runner.py). Every trial ran in an empty temporary directory with skills, slash commands, MCP servers, and user settings switched off, and with only the Read, Glob, and Grep tools. A with-skill prompt names the skill directory and that one directory is added with `--add-dir`.
- **Skill snapshot:** `plugins/tui-design/skills/tui-design`, tree SHA-256 `164c1aefd956a6e11e4155c84769ffd130986a99b5b8809ffea1e6354f6ca570`. The skill is byte-identical to `main` at `2a9210a`.
- **Source commit:** every bundle in this study ran at `2a9210a` with a clean tree (`dirty: false` in every manifest).
- **Design:** three repetitions per case and condition, with a 1,200-second trial timeout. No trial in a committed bundle failed or timed out.
- **Grading:** blind, by `claude-opus-5-5` through [`scripts/runners/claude_grader.py`](../../../scripts/runners/claude_grader.py) with protocol `v180-direct-rubric-v1`. The grader saw the question, the numbered assertions, and the answer, never the condition, host, or model. Each assertion has a grader note in `grades.json`.
- **What the sets are:** rubric-only sets written for the v1.9.0 content (issues #73–#76 and #78). Their assertions check the facts and defaults the release added, so a baseline that has not seen them is expected to score low. See *Limitations*.

| Eval set | Eval-set SHA-256 |
|---|---|
| `evals/v190-content-evals.json` | `644225a24521…` |
| `evals/v190-interaction-evals.json` | `b63cab514a3c…` |
| `evals/v190-cli-evals.json` | `e55185a2cd6f…` |
| `evals/v190-ecosystem-evals.json` | `c33641ddc1d2…` |
| `evals/v190-routing-evals.json` | `7e5a4f47cadb…` |

## Results

| Eval set | Cases | Baseline | With skill | Difference |
|---|---:|---:|---:|---:|
| `evals/v190-content-evals.json` | 6 | 45/84 (53.6%) | 80/84 (95.2%) | +41.7 pp |
| `evals/v190-interaction-evals.json` | 11 | 90/147 (61.2%) | 142/147 (96.6%) | +35.4 pp |
| `evals/v190-cli-evals.json` | 10 | 82/123 (66.7%) | 121/123 (98.4%) | +31.7 pp |
| `evals/v190-ecosystem-evals.json` | 16 | 148/186 (79.6%) | 186/186 (100.0%) | +20.4 pp |
| `evals/v190-routing-evals.json` | 4 | 25/42 (59.5%) | 42/42 (100.0%) | +40.5 pp |
| **All five sets** | 47 | **390/582 (67.0%)** | **571/582 (98.1%)** | **+31.1 pp** |

Each set is reported on its own because the sets differ in size and difficulty.

### Layout, states, and defaults (#73)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `floor-sketch-layout` | 4/15 (26.7%) | 14/15 (93.3%) | +66.7 pp |
| `state-coverage` | 11/15 (73.3%) | 14/15 (93.3%) | +20.0 pp |
| `clutter-audit-counts` | 11/15 (73.3%) | 15/15 (100.0%) | +26.7 pp |
| `status-message-timing` | 8/12 (66.7%) | 12/12 (100.0%) | +33.3 pp |
| `footer-hint-collapse` | 7/15 (46.7%) | 13/15 (86.7%) | +40.0 pp |
| `palette-and-slash` | 4/12 (33.3%) | 12/12 (100.0%) | +66.7 pp |
| **Aggregate** | **45/84 (53.6%)** | **80/84 (95.2%)** | **+41.7 pp** |

### Interaction guidance (#74)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `quit-ladder` | 10/18 (55.6%) | 18/18 (100.0%) | +44.4 pp |
| `follow-mode` | 11/18 (61.1%) | 18/18 (100.0%) | +38.9 pp |
| `selection-stability` | 5/15 (33.3%) | 13/15 (86.7%) | +53.3 pp |
| `multiline-submit` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `text-input-keys` | 10/15 (66.7%) | 13/15 (86.7%) | +20.0 pp |
| `scroll-keys` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `tree-keys` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| `modal-geometry` | 4/12 (33.3%) | 11/12 (91.7%) | +58.3 pp |
| `emoji-columns` | 6/9 (66.7%) | 9/9 (100.0%) | +33.3 pp |
| `mouse-default` | 8/12 (66.7%) | 12/12 (100.0%) | +33.3 pp |
| `diff-view-choice` | 3/12 (25.0%) | 12/12 (100.0%) | +75.0 pp |
| **Aggregate** | **90/147 (61.2%)** | **142/147 (96.6%)** | **+35.4 pp** |

### CLI defaults (#75)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `sigint-re-raise` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `json-errors` | 9/18 (50.0%) | 18/18 (100.0%) | +50.0 pp |
| `cli-testing` | 4/12 (33.3%) | 12/12 (100.0%) | +66.7 pp |
| `exit-code-scheme` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| `windows-one-shot` | 5/12 (41.7%) | 10/12 (83.3%) | +41.7 pp |
| `atomic-writes` | 12/15 (80.0%) | 15/15 (100.0%) | +20.0 pp |
| `completions-contract` | 7/12 (58.3%) | 12/12 (100.0%) | +41.7 pp |
| `pagination-config` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| `macos-config-dir` | 6/9 (66.7%) | 9/9 (100.0%) | +33.3 pp |
| `debug-env-var` | 9/9 (100.0%) | 9/9 (100.0%) | +0.0 pp |
| **Aggregate** | **82/123 (66.7%)** | **121/123 (98.4%)** | **+31.7 pp** |

### Ecosystem gaps (#76)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `go76-spinner-never-moves` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `go76-first-frame-placeholder` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `go76-lipgloss-overlay-hit` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `go76-real-cursor-ime` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| `ratatui-inline-exit-cursor` | 3/12 (25.0%) | 12/12 (100.0%) | +75.0 pp |
| `ratatui-popup-clear-shadow` | 6/12 (50.0%) | 12/12 (100.0%) | +50.0 pp |
| `ratatui-input-cursor-cells` | 9/9 (100.0%) | 9/9 (100.0%) | +0.0 pp |
| `ratatui-tui-logger-crossterm-feature` | 4/9 (44.4%) | 9/9 (100.0%) | +55.6 pp |
| `py76-textual-search-cancel` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| `py76-textual-side-by-side-panes` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| `py76-textual-in-place-reactive` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `py76-textual-sigterm-and-llm-stream` | 11/12 (91.7%) | 12/12 (100.0%) | +8.3 pp |
| `ink-virtualize-long-list` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `ink-focus-input-routing` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `ink-ctrl-c-cancel-then-quit` | 7/15 (46.7%) | 15/15 (100.0%) | +53.3 pp |
| `commander-async-action-ink` | 9/9 (100.0%) | 9/9 (100.0%) | +0.0 pp |
| **Aggregate** | **148/186 (79.6%)** | **186/186 (100.0%)** | **+20.4 pp** |

### Routing (#78)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `tmux-flicker` | 3/12 (25.0%) | 12/12 (100.0%) | +75.0 pp |
| `shift-enter-missing` | 11/12 (91.7%) | 12/12 (100.0%) | +8.3 pp |
| `status-and-unicode-routing` | 6/9 (66.7%) | 9/9 (100.0%) | +33.3 pp |
| `search-and-multiselect-routing` | 5/9 (55.6%) | 9/9 (100.0%) | +44.4 pp |
| **Aggregate** | **25/42 (59.5%)** | **42/42 (100.0%)** | **+40.5 pp** |

## Repetition variance

| Eval set | Baseline per repetition (%) | Baseline SD (pp) | With skill per repetition (%) | With-skill SD (pp) | Paired difference range |
|---|---|---:|---|---:|---|
| `content` | 64.3 / 50.0 / 46.4 | 7.72 | 96.4 / 92.9 / 96.4 | 1.68 | +32.1 to +50.0 |
| `interaction` | 61.2 / 57.1 / 65.3 | 3.33 | 95.9 / 98.0 / 95.9 | 0.96 | +30.6 to +40.8 |
| `cli` | 63.4 / 68.3 / 68.3 | 2.30 | 97.6 / 100.0 / 97.6 | 1.15 | +29.3 to +34.1 |
| `ecosystem` | 80.6 / 77.4 / 80.6 | 1.52 | 100.0 / 100.0 / 100.0 | 0.00 | +19.4 to +22.6 |
| `routing` | 50.0 / 64.3 / 64.3 | 6.73 | 100.0 / 100.0 / 100.0 | 0.00 | +35.7 to +50.0 |

SD is the population standard deviation of the per-repetition pass rates. Every paired repetition in every set favored the with-skill condition.

## What the skill did not lift

Assertions the with-skill condition still missed, with the number of the three repetitions that missed them:

| Case | Assertion | Missed |
|---|---|---:|
| `floor-sketch-layout` | 5. Draws the sketches with ASCII or narrow-width characters, or names an ASCII fallback for box drawing | 1/3 |
| `footer-hint-collapse` | 2. Orders hints by frequency of use with the most frequent first | 1/3 |
| `footer-hint-collapse` | 4. Drops the least frequent hints first as width shrinks | 1/3 |
| `state-coverage` | 4. Gives every state a next action (retry, cancel, change scope) instead of a bare message | 1/3 |
| `modal-geometry` | 2. Allows one modal at a time | 1/3 |
| `selection-stability` | 4. Does not re-sort on refresh unless the user changed the sort | 2/3 |
| `text-input-keys` | 5. Resolves the Tab collision: a field that completes owns Tab, and focus moves another way | 2/3 |
| `windows-one-shot` | 2. Says ANSI output requires enabling virtual terminal processing for Go and Rust, colorama in Python, and that Node handles it | 2/3 |

8 assertion rows were missed at least once; every other with-skill assertion passed in all three repetitions. The grader note for each miss is in `grades.json`.

## What the numbers support

Under this host, model, runner, prompt set, and three-repetition protocol, explicit use of the skill raised the assertion pass rate on every set, from 53.6–79.6% to 95.2–100.0%. The largest per-case gains are `tmux-flicker` (+75.0 pp), `ratatui-inline-exit-cursor` (+75.0 pp), `diff-view-choice` (+75.0 pp), `palette-and-slash` (+66.7 pp), `floor-sketch-layout` (+66.7 pp). 12 of 47 cases were already at 100% in the baseline and stayed there, and no case scored lower with the skill than without it.

These results don't establish a population-level effect and don't transfer to other models or hosts. They also say nothing about whether the skill activates on its own: every with-skill prompt named the skill explicitly. [#21](https://github.com/gfargo/tui-design-skill/issues/21) tracked implicit triggering, and the trigger calibration is in [`../v1.8.0-trigger-calibration/`](../v1.8.0-trigger-calibration/report.md).

## Limitations

- **Rubrics written with the content:** the assertions were written alongside the v1.9.0 changes and check what the release added. A large gap means the skill supplies those facts, not that it improves design or build quality in general. [#79](https://github.com/gfargo/tui-design-skill/issues/79) tracks measuring design and build behavior directly.
- **Same-family grader:** Claude Opus 5.5 graded every answer, including its own. The grader never saw the condition or the host, but self-preference can't be ruled out. The Codex study uses the same grader.
- **Small samples:** three repetitions per case; per-case differences of one or two assertions are within noise.

## Evidence bundles

Each directory holds the run manifest, prompts, responses, stderr, grading prompt, grades with a note for every assertion, and summary:

- [`v190-content-claude-baseline-r3/`](v190-content-claude-baseline-r3/) and [`v190-content-claude-with-skill-r3/`](v190-content-claude-with-skill-r3/)
- [`v190-interaction-claude-baseline-r3/`](v190-interaction-claude-baseline-r3/) and [`v190-interaction-claude-with-skill-r3/`](v190-interaction-claude-with-skill-r3/)
- [`v190-cli-claude-baseline-r3/`](v190-cli-claude-baseline-r3/) and [`v190-cli-claude-with-skill-r3/`](v190-cli-claude-with-skill-r3/)
- [`v190-ecosystem-claude-baseline-r3/`](v190-ecosystem-claude-baseline-r3/) and [`v190-ecosystem-claude-with-skill-r3/`](v190-ecosystem-claude-with-skill-r3/)
- [`v190-routing-claude-baseline-r3/`](v190-routing-claude-baseline-r3/) and [`v190-routing-claude-with-skill-r3/`](v190-routing-claude-with-skill-r3/)
