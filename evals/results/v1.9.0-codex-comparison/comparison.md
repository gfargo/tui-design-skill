# Codex two-condition comparison (v1.9.0)

This study measures how the v1.9.0 skill changes the Codex CLI's answers with `gpt-6.1-sol` at low reasoning effort on five new eval sets, against a no-skill baseline that uses the same host, model, runner, and prompts. It covers Codex only. The matching Claude study is in [`../v1.9.0-claude-comparison/`](../v1.9.0-claude-comparison/comparison.md).

## Protocol

- **Host and model:** OpenAI Codex CLI 0.164.0-alpha.11.1 (`codex exec`), model `gpt-6.1-sol` with `model_reasoning_effort=low`. This is a newer build than the 0.160.0 used for the v1.8.0 study. The CLI exposes neither seed nor temperature, and the bundles record its system prompt as unavailable.
- **Runner:** [`scripts/runners/codex_runner.py`](../../../scripts/runners/codex_runner.py). Every trial ran in an empty temporary directory in a read-only, ephemeral sandbox, with the user's `config.toml` ignored and web search disabled. Every user-installed skill, including any installed copy of this one, was disabled through `skills.config`; a with-skill prompt names the skill directory, which the sandbox can read.
- **Skill snapshot:** `plugins/tui-design/skills/tui-design`, tree SHA-256 `164c1aefd956a6e11e4155c84769ffd130986a99b5b8809ffea1e6354f6ca570`. The skill is byte-identical to `main` at `2a9210a`.
- **Source commit:** every bundle in this study ran at `2a9210a` with a clean tree (`dirty: false` in every manifest).
- **Design:** three repetitions per case and condition, with a 1,200-second trial timeout. No trial in a committed bundle failed or timed out. The first Codex attempt for three jobs (content with-skill and both routing conditions) hit the account's usage limit partway through; those three bundles were discarded and rerun in full at the same commit after the limit reset, so no failed trial is committed.
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
| `evals/v190-content-evals.json` | 6 | 34/84 (40.5%) | 77/84 (91.7%) | +51.2 pp |
| `evals/v190-interaction-evals.json` | 11 | 84/147 (57.1%) | 133/147 (90.5%) | +33.3 pp |
| `evals/v190-cli-evals.json` | 10 | 55/123 (44.7%) | 107/123 (87.0%) | +42.3 pp |
| `evals/v190-ecosystem-evals.json` | 16 | 141/186 (75.8%) | 175/186 (94.1%) | +18.3 pp |
| `evals/v190-routing-evals.json` | 4 | 8/42 (19.0%) | 39/42 (92.9%) | +73.8 pp |
| **All five sets** | 47 | **322/582 (55.3%)** | **531/582 (91.2%)** | **+35.9 pp** |

Each set is reported on its own because the sets differ in size and difficulty.

### Layout, states, and defaults (#73)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `floor-sketch-layout` | 5/15 (33.3%) | 15/15 (100.0%) | +66.7 pp |
| `state-coverage` | 9/15 (60.0%) | 12/15 (80.0%) | +20.0 pp |
| `clutter-audit-counts` | 7/15 (46.7%) | 15/15 (100.0%) | +53.3 pp |
| `status-message-timing` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| `footer-hint-collapse` | 1/15 (6.7%) | 11/15 (73.3%) | +66.7 pp |
| `palette-and-slash` | 3/12 (25.0%) | 12/12 (100.0%) | +75.0 pp |
| **Aggregate** | **34/84 (40.5%)** | **77/84 (91.7%)** | **+51.2 pp** |

### Interaction guidance (#74)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `quit-ladder` | 7/18 (38.9%) | 17/18 (94.4%) | +55.6 pp |
| `follow-mode` | 10/18 (55.6%) | 14/18 (77.8%) | +22.2 pp |
| `selection-stability` | 6/15 (40.0%) | 13/15 (86.7%) | +46.7 pp |
| `multiline-submit` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `text-input-keys` | 7/15 (46.7%) | 11/15 (73.3%) | +26.7 pp |
| `scroll-keys` | 6/12 (50.0%) | 12/12 (100.0%) | +50.0 pp |
| `tree-keys` | 8/12 (66.7%) | 12/12 (100.0%) | +33.3 pp |
| `modal-geometry` | 3/12 (25.0%) | 9/12 (75.0%) | +50.0 pp |
| `emoji-columns` | 6/9 (66.7%) | 9/9 (100.0%) | +33.3 pp |
| `mouse-default` | 10/12 (83.3%) | 12/12 (100.0%) | +16.7 pp |
| `diff-view-choice` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| **Aggregate** | **84/147 (57.1%)** | **133/147 (90.5%)** | **+33.3 pp** |

### CLI defaults (#75)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `sigint-re-raise` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `json-errors` | 8/18 (44.4%) | 18/18 (100.0%) | +55.6 pp |
| `cli-testing` | 3/12 (25.0%) | 9/12 (75.0%) | +50.0 pp |
| `exit-code-scheme` | 3/12 (25.0%) | 12/12 (100.0%) | +75.0 pp |
| `windows-one-shot` | 3/12 (25.0%) | 6/12 (50.0%) | +25.0 pp |
| `atomic-writes` | 5/15 (33.3%) | 11/15 (73.3%) | +40.0 pp |
| `completions-contract` | 5/12 (41.7%) | 12/12 (100.0%) | +58.3 pp |
| `pagination-config` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| `macos-config-dir` | 3/9 (33.3%) | 6/9 (66.7%) | +33.3 pp |
| `debug-env-var` | 4/9 (44.4%) | 9/9 (100.0%) | +55.6 pp |
| **Aggregate** | **55/123 (44.7%)** | **107/123 (87.0%)** | **+42.3 pp** |

### Ecosystem gaps (#76)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `go76-spinner-never-moves` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `go76-first-frame-placeholder` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `go76-lipgloss-overlay-hit` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `go76-real-cursor-ime` | 7/12 (58.3%) | 12/12 (100.0%) | +41.7 pp |
| `ratatui-inline-exit-cursor` | 1/12 (8.3%) | 9/12 (75.0%) | +66.7 pp |
| `ratatui-popup-clear-shadow` | 6/12 (50.0%) | 12/12 (100.0%) | +50.0 pp |
| `ratatui-input-cursor-cells` | 9/9 (100.0%) | 9/9 (100.0%) | +0.0 pp |
| `ratatui-tui-logger-crossterm-feature` | 5/9 (55.6%) | 8/9 (88.9%) | +33.3 pp |
| `py76-textual-search-cancel` | 9/12 (75.0%) | 9/12 (75.0%) | +0.0 pp |
| `py76-textual-side-by-side-panes` | 9/12 (75.0%) | 9/12 (75.0%) | +0.0 pp |
| `py76-textual-in-place-reactive` | 11/12 (91.7%) | 12/12 (100.0%) | +8.3 pp |
| `py76-textual-sigterm-and-llm-stream` | 10/12 (83.3%) | 12/12 (100.0%) | +16.7 pp |
| `ink-virtualize-long-list` | 11/12 (91.7%) | 12/12 (100.0%) | +8.3 pp |
| `ink-focus-input-routing` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `ink-ctrl-c-cancel-then-quit` | 6/15 (40.0%) | 14/15 (93.3%) | +53.3 pp |
| `commander-async-action-ink` | 9/9 (100.0%) | 9/9 (100.0%) | +0.0 pp |
| **Aggregate** | **141/186 (75.8%)** | **175/186 (94.1%)** | **+18.3 pp** |

### Routing (#78)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `tmux-flicker` | 3/12 (25.0%) | 11/12 (91.7%) | +66.7 pp |
| `shift-enter-missing` | 2/12 (16.7%) | 10/12 (83.3%) | +66.7 pp |
| `status-and-unicode-routing` | 3/9 (33.3%) | 9/9 (100.0%) | +66.7 pp |
| `search-and-multiselect-routing` | 0/9 (0.0%) | 9/9 (100.0%) | +100.0 pp |
| **Aggregate** | **8/42 (19.0%)** | **39/42 (92.9%)** | **+73.8 pp** |

## Repetition variance

| Eval set | Baseline per repetition (%) | Baseline SD (pp) | With skill per repetition (%) | With-skill SD (pp) | Paired difference range |
|---|---|---:|---|---:|---|
| `content` | 42.9 / 46.4 / 32.1 | 6.07 | 92.9 / 92.9 / 89.3 | 1.68 | +46.4 to +57.1 |
| `interaction` | 63.3 / 53.1 / 55.1 | 4.41 | 87.8 / 91.8 / 91.8 | 1.92 | +24.5 to +38.8 |
| `cli` | 41.5 / 48.8 / 43.9 | 3.04 | 85.4 / 90.2 / 85.4 | 2.30 | +41.5 to +43.9 |
| `ecosystem` | 74.2 / 72.6 / 80.6 | 3.48 | 95.2 / 95.2 / 91.9 | 1.52 | +11.3 to +22.6 |
| `routing` | 21.4 / 14.3 / 21.4 | 3.37 | 85.7 / 92.9 / 100.0 | 5.83 | +64.3 to +78.6 |

SD is the population standard deviation of the per-repetition pass rates. Every paired repetition in every set favored the with-skill condition.

## What the skill did not lift

Assertions the with-skill condition still missed, with the number of the three repetitions that missed them:

| Case | Assertion | Missed |
|---|---|---:|
| `footer-hint-collapse` | 1. Shows one rendered footer line at 80 columns and a shorter line at 40 columns | 1/3 |
| `footer-hint-collapse` | 4. Drops the least frequent hints first as width shrinks | 3/3 |
| `state-coverage` | 3. Says a stale or disconnected view keeps the last-known-good data visible, dimmed, with an age or 'stale' marker | 3/3 |
| `follow-mode` | 5. Caps retained lines with a ring buffer and says when the oldest lines were dropped | 1/3 |
| `follow-mode` | 6. Offers a wrap toggle, rather than always wrapping or always truncating | 3/3 |
| `modal-geometry` | 2. Allows one modal at a time | 3/3 |
| `quit-ladder` | 6. Confirms a quit only when it loses something (unsaved edits or running work), with a default of No, and never asks on an idle quit | 1/3 |
| `selection-stability` | 1. Tracks the selection by a stable ID rather than a row index and re-resolves it after refresh, sort, and filter | 1/3 |
| `selection-stability` | 5. Offers a freeze or pause key shown in the footer, with a PAUSED marker and a count of pending changes | 1/3 |
| `text-input-keys` | 2. Notes that Ctrl+A collides with GNU screen's prefix | 2/3 |
| `text-input-keys` | 5. Resolves the Tab collision: a field that completes owns Tab, and focus moves another way | 2/3 |
| `atomic-writes` | 2. Explains why the temp file must be on the same filesystem as the target | 2/3 |
| `atomic-writes` | 5. Notes Windows replace is best effort rather than guaranteed atomic | 2/3 |
| `cli-testing` | 4. Uses golden files for text but not color escapes | 3/3 |
| `macos-config-dir` | 3. Notes that other helpers (Rust dirs/directories) behave the same way | 3/3 |
| `windows-one-shot` | 1. Says Windows has no SIGPIPE, SIGHUP, or 128+N exit codes and treats a closed pipe as a write error | 3/3 |
| `windows-one-shot` | 2. Says ANSI output requires enabling virtual terminal processing for Go and Rust, colorama in Python, and that Node handles it | 3/3 |
| `ink-ctrl-c-cancel-then-quit` | 4. Keeps that Ctrl+C handler always active (not focus-gated), because with no active input hook raw mode is off and Ctrl+C becomes SIGINT again | 1/3 |
| `py76-textual-search-cancel` | 4. Mentions exit_on_error=False and handling the ERROR state in on_worker_state_changed (or event.worker.error) if a failing search must not quit the app | 3/3 |
| `py76-textual-side-by-side-panes` | 3. States that Vertical, Horizontal and Grid expand to fill (1fr width and height) while VerticalGroup, HorizontalGroup and ItemGrid are height: auto and hug their content | 3/3 |
| `ratatui-inline-exit-cursor` | 3. Prints permanent lines above the UI with Terminal::insert_before, and optionally mentions Ratatui's scrolling-regions feature to avoid clearing and redrawing the viewport | 3/3 |
| `ratatui-tui-logger-crossterm-feature` | 2. Says the crossterm and termion features of tui-logger only gate its bundled demo example (and forward to ratatui's backend feature) | 1/3 |
| `shift-enter-missing` | 2. Notes tmux needs the extended-keys option, which is off by default | 2/3 |
| `tmux-flicker` | 1. Recommends wrapping each frame in synchronized output (mode 2026) so the terminal paints it at once, and detecting support with DECRQM | 1/3 |

24 assertion rows were missed at least once; every other with-skill assertion passed in all three repetitions. The grader note for each miss is in `grades.json`.

## What the numbers support

Under this host, model, runner, prompt set, and three-repetition protocol, explicit use of the skill raised the assertion pass rate on every set, from 19.0–75.8% to 87.0–94.1%. The largest per-case gains are `search-and-multiselect-routing` (+100.0 pp), `palette-and-slash` (+75.0 pp), `exit-code-scheme` (+75.0 pp), `status-and-unicode-routing` (+66.7 pp), `shift-enter-missing` (+66.7 pp). 8 of 47 cases were already at 100% in the baseline and stayed there, and no case scored lower with the skill than without it.

These results don't establish a population-level effect and don't transfer to other models or hosts. They also say nothing about whether the skill activates on its own: every with-skill prompt named the skill explicitly. [#21](https://github.com/gfargo/tui-design-skill/issues/21) tracked implicit triggering, and the trigger calibration is in [`../v1.8.0-trigger-calibration/`](../v1.8.0-trigger-calibration/report.md).

## Limitations

- **Rubrics written with the content:** the assertions were written alongside the v1.9.0 changes and check what the release added. A large gap means the skill supplies those facts, not that it improves design or build quality in general. [#79](https://github.com/gfargo/tui-design-skill/issues/79) tracks measuring design and build behavior directly.
- **Same-family grader:** Claude Opus 5.5 graded every answer, including the Codex answers. The grader never saw the condition or the host, but self-preference can't be ruled out, and a Claude grader may favor Claude-style answers on both conditions here.
- **Small samples:** three repetitions per case; per-case differences of one or two assertions are within noise.
- **CLI build:** this study used Codex CLI 0.164.0-alpha.11.1; the v1.8.0 Codex study used 0.160.0, so the two Codex studies are not a controlled comparison of the skill versions.
- **Routing baseline:** the routing set asks for details such as tmux 3.7's synchronized-output support and the `extended-keys` default. The baseline scored lowest here, which reflects facts newer than the model rather than weak reasoning.

## Evidence bundles

Each directory holds the run manifest, prompts, responses, stderr, grading prompt, grades with a note for every assertion, and summary:

- [`v190-content-codex-baseline-r3/`](v190-content-codex-baseline-r3/) and [`v190-content-codex-with-skill-r3/`](v190-content-codex-with-skill-r3/)
- [`v190-interaction-codex-baseline-r3/`](v190-interaction-codex-baseline-r3/) and [`v190-interaction-codex-with-skill-r3/`](v190-interaction-codex-with-skill-r3/)
- [`v190-cli-codex-baseline-r3/`](v190-cli-codex-baseline-r3/) and [`v190-cli-codex-with-skill-r3/`](v190-cli-codex-with-skill-r3/)
- [`v190-ecosystem-codex-baseline-r3/`](v190-ecosystem-codex-baseline-r3/) and [`v190-ecosystem-codex-with-skill-r3/`](v190-ecosystem-codex-with-skill-r3/)
- [`v190-routing-codex-baseline-r3/`](v190-routing-codex-baseline-r3/) and [`v190-routing-codex-with-skill-r3/`](v190-routing-codex-with-skill-r3/)
