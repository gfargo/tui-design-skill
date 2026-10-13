# Claude two-condition comparison (v1.8.0)

This study measures how the v1.8.0 skill changes Claude Opus 5.5's answers on six eval sets, against a no-skill baseline that uses the same host, model, runner, and prompts. It covers Claude only. The matching Codex study is in [`../v1.8.0-codex-comparison/`](../v1.8.0-codex-comparison/comparison.md); the hosts used different models and settings, so don't add their numbers together or rank them against each other.

## Protocol

- **Host and model:** Claude Code 2.1.295 in non-interactive mode (`claude -p`), model `claude-opus-5-5` at its default effort. The CLI exposes neither seed nor temperature, and the bundles record its system prompt as unavailable.
- **Runner:** [`scripts/runners/claude_runner.py`](../../../scripts/runners/claude_runner.py). Every trial ran in an empty temporary directory with skills, slash commands, MCP servers, and user settings switched off, and with only the Read, Glob, and Grep tools. Baseline prompts were unchanged. With-skill prompts differed only by the harness's instruction to use the skill at its recorded path, and the runner gave the model read access to that one directory with `--add-dir`.
- **Skill snapshot:** `plugins/tui-design/skills/tui-design`, tree SHA-256 `6f706f2144bf137cf0ace17b44d459ee7431c6fdfef0869c2d35b1d195a758f7`. The skill and every eval set are byte-identical to the `v1.8.0` tag.
- **Source commits:** the v1.7.3 baseline ran at `8988b14` and every other bundle at `d39172e`. The two commits differ only by the grader script and its grading prompt. Every manifest records a clean tree.
- **Design:** three repetitions per case and condition, with a 1,200-second trial timeout. No trial failed or timed out.
- **Grading:** blind, by `claude-opus-5-5` through [`scripts/runners/claude_grader.py`](../../../scripts/runners/claude_grader.py) with protocol `v180-direct-rubric-v1`. The grader saw the question, the numbered assertions, and the answer, never the condition, host, or model, and it wrote a one-sentence note for every assertion. All twelve schema-v5 bundles validate with `--require-completed`.

| Eval set | Eval-set SHA-256 | Commit (baseline / with skill) |
|---|---|---|
| `evals/v173-correction-evals.json` | `5e5a1e0e05cf…` | `8988b14` / `d39172e` |
| `evals/v171-correction-evals.json` | `eba9db07f549…` | `d39172e` / `d39172e` |
| `evals/v170-lifecycle-evals.json` | `a98562be4f5e…` | `d39172e` / `d39172e` |
| `evals/v180-terminal-modes-evals.json` | `153026b43088…` | `d39172e` / `d39172e` |
| `evals/v180-accessibility-evals.json` | `c2cd8c5df456…` | `d39172e` / `d39172e` |
| `evals/v180-l10n-environments-evals.json` | `e1a6ec31f5d9…` | `d39172e` / `d39172e` |

## Results

| Eval set | Cases | Baseline | With skill | Difference |
|---|---:|---:|---:|---:|
| `evals/v173-correction-evals.json` | 9 | 90/111 (81.1%) | 110/111 (99.1%) | +18.0 pp |
| `evals/v171-correction-evals.json` | 8 | 75/96 (78.1%) | 93/96 (96.9%) | +18.8 pp |
| `evals/v170-lifecycle-evals.json` | 5 | 56/75 (74.7%) | 75/75 (100.0%) | +25.3 pp |
| `evals/v180-terminal-modes-evals.json` | 5 | 45/57 (78.9%) | 57/57 (100.0%) | +21.1 pp |
| `evals/v180-accessibility-evals.json` | 4 | 42/57 (73.7%) | 55/57 (96.5%) | +22.8 pp |
| `evals/v180-l10n-environments-evals.json` | 4 | 42/45 (93.3%) | 45/45 (100.0%) | +6.7 pp |

Each set is reported on its own because the sets differ in size and difficulty.

### v1.7.3 corrections

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `lazygit-undo-scope` | 8/12 (66.7%) | 12/12 (100.0%) | +33.3 pp |
| `raw-mode-reserved-keys` | 12/12 (100.0%) | 11/12 (91.7%) | -8.3 pp |
| `huh-v2-theme` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `bubbletea-background-query` | 11/12 (91.7%) | 12/12 (100.0%) | +8.3 pp |
| `ratatui-async-input` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `textual-computed-reactive` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `ink-suspend-node20` | 5/15 (33.3%) | 15/15 (100.0%) | +66.7 pp |
| `path-truncation-side` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| `smart-case-defaults` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| **Aggregate** | **90/111 (81.1%)** | **110/111 (99.1%)** | **+18.0 pp** |

The largest gain is `ink-suspend-node20`. No baseline answer said that Ink 7 and later need Node 22 or that Ink 7.1 added `suspendTerminal`; all three said Ink has no suspend API. Both facts are newer than the model's training data. The baseline also gave lazygit's redo key as Ctrl+Z in two of three repetitions (it is Shift+Z), never said when end truncation is still right, and never mentioned match counts for a filter. The one with-skill miss is a wording slip: a repetition wrote that "helix binds it too" in a sentence about saving with Ctrl+S, while the skill says Helix binds Ctrl+S to `save_selection`.

### v1.7.1 corrections

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `rich-traceback-install` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `lazygit-config-format` | 9/12 (75.0%) | 9/12 (75.0%) | +0.0 pp |
| `reserved-ctrl-s-save` | 9/12 (75.0%) | 12/12 (100.0%) | +25.0 pp |
| `btop-refresh-cadence` | 8/12 (66.7%) | 12/12 (100.0%) | +33.3 pp |
| `wish-v2-session-options` | 10/12 (83.3%) | 12/12 (100.0%) | +16.7 pp |
| `spinner-delay-contract` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `tview-goroutine-draw` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `do-not-track-adoption` | 3/12 (25.0%) | 12/12 (100.0%) | +75.0 pp |
| **Aggregate** | **75/96 (78.1%)** | **93/96 (96.9%)** | **+18.8 pp** |

`do-not-track-adoption` moved from 3/12 to 12/12. The baseline never named a real `DO_NOT_TRACK` adopter, and two of three answers hedged on whether Homebrew, Gatsby, and the .NET SDK honor it. With the skill, every answer named gh, netdata, or tilt and recommended a tool-specific opt-out. The baseline also never said to show a Ctrl+S save binding in the app's help, and never separated widget independence from per-widget timers in the btop case. `lazygit-config-format` failed the same assertion in every trial of both conditions; see [Limitations](#limitations).

### v1.7 lifecycle

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `bubble-tea-editor-handoff` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `ratatui-editor-reader` | 15/15 (100.0%) | 15/15 (100.0%) | +0.0 pp |
| `textual-portable-suspension` | 15/15 (100.0%) | 15/15 (100.0%) | +0.0 pp |
| `ink-suspend-terminal` | 0/15 (0.0%) | 15/15 (100.0%) | +100.0 pp |
| `cross-framework-signal-boundaries` | 14/18 (77.8%) | 18/18 (100.0%) | +22.2 pp |
| **Aggregate** | **56/75 (74.7%)** | **75/75 (100.0%)** | **+25.3 pp** |

Two cases account for the whole difference. Every baseline answer to the Ink case recommended unmounting and re-rendering around the editor and never mentioned `useApp().suspendTerminal`, so it failed all five assertions. In the cross-framework case, two baseline repetitions didn't say that Ink's `exitOnCtrlC` handles raw input rather than SIGTERM, and two gave no Windows path for job-control suspend. Bubble Tea, Ratatui, and Textual were saturated in both conditions.

This set's rubric changed after the v1.7.0 Codex comparison (eval-set SHA-256 `a98562be…` here, `1bab1181…` there), and the skill, host, and model differ too, so the two lifecycle studies are not comparable.

### Terminal modes and protocols (v1.8.0)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `bracketed-paste-multiline` | 10/12 (83.3%) | 12/12 (100.0%) | +16.7 pp |
| `sync-output-tearing` | 11/12 (91.7%) | 12/12 (100.0%) | +8.3 pp |
| `kitty-keyboard-shift-enter` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `background-query-ssh` | 7/12 (58.3%) | 12/12 (100.0%) | +41.7 pp |
| `cursor-title-restore` | 5/9 (55.6%) | 9/9 (100.0%) | +44.4 pp |
| **Aggregate** | **45/57 (78.9%)** | **57/57 (100.0%)** | **+21.1 pp** |

No baseline answer turned mode 2031 off on exit or before handing the terminal to a child process, and none acknowledged that the original cursor shape can't be queried or that xterm treats shape 0 as a blinking block. Every with-skill answer covered both.

### Accessibility (v1.8.0)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `bubbletea-form-screen-reader` | 11/15 (73.3%) | 15/15 (100.0%) | +26.7 pp |
| `no-tui-output-contract` | 15/18 (83.3%) | 18/18 (100.0%) | +16.7 pp |
| `textual-serve-accessibility` | 4/9 (44.4%) | 9/9 (100.0%) | +55.6 pp |
| `ink-screen-reader-live-region` | 12/15 (80.0%) | 13/15 (86.7%) | +6.7 pp |
| **Aggregate** | **42/57 (73.7%)** | **55/57 (96.5%)** | **+22.8 pp** |

No baseline answer said that `textual serve` is not an accessibility path because its xterm.js canvas runs with screen-reader mode off; every with-skill answer did. The baseline also never said that Bubble Tea has no screen-reader support, never said that `--no-tui` prompts and progress belong on stderr while results stay on stdout, and never said that Ink can't detect a screen reader on its own. Both with-skill misses are in the Ink case: two answers mentioned `aria-label` but didn't recommend it for visual-only elements.

### Localization and terminal environments (v1.8.0)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `translation-growth-60-columns` | 12/15 (80.0%) | 15/15 (100.0%) | +20.0 pp |
| `tmux-prefix-collision` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `ambiguous-width-borders` | 9/9 (100.0%) | 9/9 (100.0%) | +0.0 pp |
| `locale-machine-output` | 9/9 (100.0%) | 9/9 (100.0%) | +0.0 pp |
| **Aggregate** | **42/45 (93.3%)** | **45/45 (100.0%)** | **+6.7 pp** |

The baseline was already near the ceiling. Its only repeated miss was the warning that short strings such as column headers and footer hints grow the most in translation.

## Repetition variance

| Eval set | Baseline per repetition (%) | Baseline SD (pp) | With skill per repetition (%) | With-skill SD (pp) | Paired difference range |
|---|---|---:|---|---:|---|
| `v173-correction` | 81.1 / 78.4 / 83.8 | 2.21 | 100.0 / 100.0 / 97.3 | 1.27 | +13.5 to +21.6 |
| `v171-correction` | 78.1 / 81.2 / 75.0 | 2.55 | 96.9 / 96.9 / 96.9 | 0.00 | +15.6 to +21.9 |
| `v170-lifecycle` | 72.0 / 80.0 / 72.0 | 3.77 | 100.0 / 100.0 / 100.0 | 0.00 | +20.0 to +28.0 |
| `terminal-modes` | 84.2 / 73.7 / 78.9 | 4.30 | 100.0 / 100.0 / 100.0 | 0.00 | +15.8 to +26.3 |
| `accessibility` | 68.4 / 73.7 / 78.9 | 4.30 | 94.7 / 100.0 / 94.7 | 2.48 | +15.8 to +26.3 |
| `l10n-environments` | 93.3 / 93.3 / 93.3 | 0.00 | 100.0 / 100.0 / 100.0 | 0.00 | +6.7 to +6.7 |

SD is the population standard deviation of the per-repetition pass rates. Every paired repetition in every set favored the with-skill condition. Baseline rates moved by up to 10.5 points between repetitions of one set; with the skill, four of six sets scored the same in every repetition.

## What the numbers support

Under this host, model, runner, prompt set, and three-repetition protocol, explicit use of the skill raised the assertion pass rate on every set, from 73.7–93.3% to 96.5–100%. The gain comes from facts the model didn't have or didn't volunteer: releases newer than its training data (Ink 7.1 and 8), corrected premises (btop's single refresh interval, `DO_NOT_TRACK` adoption), and terminal cleanup rules that no framework enforces. Cases the baseline already answered well stayed at or near 100%.

These results don't establish a population-level effect and don't transfer to other models or hosts. They also say nothing about whether the skill activates on its own: every with-skill prompt named the skill explicitly. [#21](https://github.com/gfargo/tui-design-skill/issues/21) tracks implicit triggering.

## Limitations

- **Same-family grader:** Claude Opus 5.5 graded Claude Opus 5.5's answers. The grader never saw the condition, but self-preference can't be ruled out. The Codex study uses the same grader, so any bias toward Claude-style answers would affect both of its conditions.
- **Ceiling:** five of six with-skill conditions scored 96.5% or higher, so these sets can't show further improvement for this model.
- **Rubric conflict:** `lazygit-config-format` assertion 4 asks the answer to choose a config format from the app's own needs, but the prompt asks to mirror lazygit's conventions, and the skill's *Configuration formats* list never states that rule. Every trial on both hosts and in both conditions failed it. The rubric was left unchanged for this study so the recorded eval-set hash stays valid, and was corrected afterward: the assertion now checks that the answer doesn't present one format as the TUI standard.
- **Knowledge cutoff:** the two largest case gains (`ink-suspend-node20` and `ink-suspend-terminal`) test facts released after the model's training data. They show the skill supplying current facts, not better reasoning.

## Evidence bundles

Each directory holds the run manifest, prompts, responses, stderr, grading prompt, grades with a note for every assertion, and summary:

- [`v180-v173-correction-claude-baseline-r3/`](v180-v173-correction-claude-baseline-r3/) and [`v180-v173-correction-claude-with-skill-r3/`](v180-v173-correction-claude-with-skill-r3/)
- [`v180-v171-correction-claude-baseline-r3/`](v180-v171-correction-claude-baseline-r3/) and [`v180-v171-correction-claude-with-skill-r3/`](v180-v171-correction-claude-with-skill-r3/)
- [`v180-v170-lifecycle-claude-baseline-r3/`](v180-v170-lifecycle-claude-baseline-r3/) and [`v180-v170-lifecycle-claude-with-skill-r3/`](v180-v170-lifecycle-claude-with-skill-r3/)
- [`v180-terminal-modes-claude-baseline-r3/`](v180-terminal-modes-claude-baseline-r3/) and [`v180-terminal-modes-claude-with-skill-r3/`](v180-terminal-modes-claude-with-skill-r3/)
- [`v180-accessibility-claude-baseline-r3/`](v180-accessibility-claude-baseline-r3/) and [`v180-accessibility-claude-with-skill-r3/`](v180-accessibility-claude-with-skill-r3/)
- [`v180-l10n-environments-claude-baseline-r3/`](v180-l10n-environments-claude-baseline-r3/) and [`v180-l10n-environments-claude-with-skill-r3/`](v180-l10n-environments-claude-with-skill-r3/)
