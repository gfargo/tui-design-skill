# Codex two-condition comparison (v1.8.0)

This study measures how the v1.8.0 skill changes the Codex CLI's answers with `gpt-6.1-sol` at low reasoning effort on five eval sets, against a no-skill baseline that uses the same host, model, runner, and prompts. It covers Codex only. The matching Claude study is in [`../v1.8.0-claude-comparison/`](../v1.8.0-claude-comparison/comparison.md); the hosts used different models and settings, so don't add their numbers together or rank them against each other.

## Protocol

- **Host and model:** OpenAI Codex CLI 0.160.0 (`codex exec`), model `gpt-6.1-sol` with `model_reasoning_effort=low`. The CLI exposes neither seed nor temperature, and the bundles record its system prompt as unavailable.
- **Runner:** [`scripts/runners/codex_runner.py`](../../../scripts/runners/codex_runner.py). Every trial ran in an empty temporary directory in a read-only, ephemeral sandbox, with the user's `config.toml` ignored and web search disabled. Every user-installed skill, including the installed copy of tui-design, was disabled through `skills.config`; Codex's bundled system skills stayed available in both conditions. Baseline prompts were unchanged. With-skill prompts differed only by the harness's instruction to use the skill at its recorded path. Each trial's stderr keeps Codex's transcript, including every skill file a with-skill trial read.
- **Skill snapshot:** `plugins/tui-design/skills/tui-design`, tree SHA-256 `6f706f2144bf137cf0ace17b44d459ee7431c6fdfef0869c2d35b1d195a758f7`. The skill and every eval set are byte-identical to the `v1.8.0` tag.
- **Source commits:** the v1.7.3 baseline ran at `8988b14` and every other bundle at `d39172e`, except as noted for the localization set below. The commits differ only by the grader script and its grading prompt. Every manifest records a clean tree.
- **Design:** three repetitions per case and condition, with a 1,200-second trial timeout. No trial in a committed bundle failed or timed out.
- **Grading:** blind, by `claude-opus-5-5` through [`scripts/runners/claude_grader.py`](../../../scripts/runners/claude_grader.py) with protocol `v180-direct-rubric-v1`, the same grader as the Claude study. The grader saw the question, the numbered assertions, and the answer, never the condition, host, or model, and it wrote a one-sentence note for every assertion. Every committed schema-v5 bundle validates with `--require-completed`.

The v1.7 lifecycle set was not rerun here. The earlier Codex lifecycle study in [`../v1.7.0-lifecycle-comparison/`](../v1.7.0-lifecycle-comparison/comparison.md) used a different model (`gpt-5.6-terra`) and an older version of that eval set.

| Eval set | Eval-set SHA-256 | Commit (baseline / with skill) |
|---|---|---|
| `evals/v173-correction-evals.json` | `5e5a1e0e05cf…` | `8988b14` / `d39172e` |
| `evals/v171-correction-evals.json` | `eba9db07f549…` | `d39172e` / `d39172e` |
| `evals/v180-terminal-modes-evals.json` | `153026b43088…` | `d39172e` / `d39172e` |
| `evals/v180-accessibility-evals.json` | `c2cd8c5df456…` | `d39172e` / `d39172e` |
| `evals/v180-l10n-environments-evals.json` | `e1a6ec31f5d9…` | `d39172e` / pending |

## Results

| Eval set | Cases | Baseline | With skill | Difference |
|---|---:|---:|---:|---:|
| `evals/v173-correction-evals.json` | 9 | 80/111 (72.1%) | 105/111 (94.6%) | +22.5 pp |
| `evals/v171-correction-evals.json` | 8 | 65/96 (67.7%) | 87/96 (90.6%) | +22.9 pp |
| `evals/v180-terminal-modes-evals.json` | 5 | 37/57 (64.9%) | 55/57 (96.5%) | +31.6 pp |
| `evals/v180-accessibility-evals.json` | 4 | 28/57 (49.1%) | 49/57 (86.0%) | +36.8 pp |
| `evals/v180-l10n-environments-evals.json` | 4 | 27/45 (60.0%) | pending | pending |

Each set is reported on its own because the sets differ in size and difficulty.

### v1.7.3 corrections

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `lazygit-undo-scope` | 6/12 (50.0%) | 12/12 (100.0%) | +50.0 pp |
| `raw-mode-reserved-keys` | 6/12 (50.0%) | 12/12 (100.0%) | +50.0 pp |
| `huh-v2-theme` | 10/12 (83.3%) | 12/12 (100.0%) | +16.7 pp |
| `bubbletea-background-query` | 8/12 (66.7%) | 12/12 (100.0%) | +33.3 pp |
| `ratatui-async-input` | 10/12 (83.3%) | 12/12 (100.0%) | +16.7 pp |
| `textual-computed-reactive` | 10/12 (83.3%) | 12/12 (100.0%) | +16.7 pp |
| `ink-suspend-node20` | 12/15 (80.0%) | 15/15 (100.0%) | +20.0 pp |
| `path-truncation-side` | 9/12 (75.0%) | 9/12 (75.0%) | +0.0 pp |
| `smart-case-defaults` | 9/12 (75.0%) | 9/12 (75.0%) | +0.0 pp |
| **Aggregate** | **80/111 (72.1%)** | **105/111 (94.6%)** | **+22.5 pp** |

Every baseline answer gave lazygit's redo key as Ctrl+Z (it is Shift+Z). No baseline answer warned that users expect Ctrl+C to cancel or quit, called Ctrl+S-to-save an established convention, kept `HasDarkBackground` for standalone Lipgloss, or said that Node 20 reached end-of-life. With the skill, seven of nine cases scored full marks. The remaining six misses repeat in all three repetitions: the answers didn't say when end truncation is still right, and didn't mention keeping a filter responsive or showing match counts. Those are proactive additions a low-effort answer to a narrow question leaves out.

### v1.7.1 corrections

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `rich-traceback-install` | 10/12 (83.3%) | 12/12 (100.0%) | +16.7 pp |
| `lazygit-config-format` | 9/12 (75.0%) | 9/12 (75.0%) | +0.0 pp |
| `reserved-ctrl-s-save` | 4/12 (33.3%) | 10/12 (83.3%) | +50.0 pp |
| `btop-refresh-cadence` | 6/12 (50.0%) | 12/12 (100.0%) | +50.0 pp |
| `wish-v2-session-options` | 10/12 (83.3%) | 11/12 (91.7%) | +8.3 pp |
| `spinner-delay-contract` | 11/12 (91.7%) | 12/12 (100.0%) | +8.3 pp |
| `tview-goroutine-draw` | 12/12 (100.0%) | 12/12 (100.0%) | +0.0 pp |
| `do-not-track-adoption` | 3/12 (25.0%) | 9/12 (75.0%) | +50.0 pp |
| **Aggregate** | **65/96 (67.7%)** | **87/96 (90.6%)** | **+22.9 pp** |

Every baseline answer to the btop case accepted the prompt's false premise of separate 100 ms and 2 s refresh rates; with the skill, every answer said btop has one shared `update_ms` setting. No baseline answer explained that raw mode disables XON/XOFF flow control, so Ctrl+S reaches the app. `do-not-track-adoption` improved on the opt-out design but not on adopters. In all three with-skill trials the transcript shows Codex reading the `cli-basics.md` paragraph that names netdata, tilt, and the GitHub CLI, yet no answer named a real adopter. `lazygit-config-format` failed the same assertion in every trial of both conditions; see [Limitations](#limitations).

### Terminal modes and protocols (v1.8.0)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `bracketed-paste-multiline` | 7/12 (58.3%) | 11/12 (91.7%) | +33.3 pp |
| `sync-output-tearing` | 10/12 (83.3%) | 12/12 (100.0%) | +16.7 pp |
| `kitty-keyboard-shift-enter` | 10/12 (83.3%) | 11/12 (91.7%) | +8.3 pp |
| `background-query-ssh` | 7/12 (58.3%) | 12/12 (100.0%) | +41.7 pp |
| `cursor-title-restore` | 3/9 (33.3%) | 9/9 (100.0%) | +66.7 pp |
| **Aggregate** | **37/57 (64.9%)** | **55/57 (96.5%)** | **+31.6 pp** |

No baseline answer acknowledged that the original cursor shape can't be queried, warned that terminals which ignore the title stack lose the old title, said that crossterm and Ratatui leave bracketed paste off by default, or turned mode 2031 off on exit. Every with-skill answer to the cursor, title, and background-query cases covered them. The two with-skill misses: one answer didn't say that bracketed paste is off by default, and one didn't tie the Shift+Enter hint to the terminal's enhanced-keyboard report.

### Accessibility (v1.8.0)

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| `bubbletea-form-screen-reader` | 7/15 (46.7%) | 13/15 (86.7%) | +40.0 pp |
| `no-tui-output-contract` | 11/18 (61.1%) | 18/18 (100.0%) | +38.9 pp |
| `textual-serve-accessibility` | 2/9 (22.2%) | 6/9 (66.7%) | +44.4 pp |
| `ink-screen-reader-live-region` | 8/15 (53.3%) | 12/15 (80.0%) | +26.7 pp |
| **Aggregate** | **28/57 (49.1%)** | **49/57 (86.0%)** | **+36.8 pp** |

This set had the lowest baseline. Every baseline answer to the `textual serve` question said no, but none gave the reason (xterm.js paints a canvas with screen-reader mode off), and two suggested the browser terminal might expose its output. No baseline answer explained that Ink's screen-reader mode still rewrites the whole live region, that Bubble Tea has no screen-reader support, or that a full-screen form's repaints are re-read. With the skill, the `--no-tui` contract reached 18/18. The remaining misses are omissions: no with-skill answer said that Textual itself has no screen-reader support, and two Ink answers mentioned `aria-label` without recommending it for visual-only elements.

### Localization and terminal environments (v1.8.0)

The baseline scored 27/45 (60.0%): `translation-growth-60-columns` 9/15, `tmux-prefix-collision` 7/12, `ambiguous-width-borders` 6/9, and `locale-machine-output` 5/9. The first with-skill attempt stopped after 8 of 12 trials when the Codex account reached its usage limit. That partial attempt is not used. The condition is being rerun in full after the limit resets, and this section will report it.

## Repetition variance

| Eval set | Baseline per repetition (%) | Baseline SD (pp) | With skill per repetition (%) | With-skill SD (pp) | Paired difference range |
|---|---|---:|---|---:|---|
| `v173-correction` | 75.7 / 70.3 / 70.3 | 2.55 | 94.6 / 94.6 / 94.6 | 0.00 | +18.9 to +24.3 |
| `v171-correction` | 71.9 / 65.6 / 65.6 | 2.95 | 93.8 / 90.6 / 87.5 | 2.55 | +21.9 to +25.0 |
| `terminal-modes` | 57.9 / 68.4 / 68.4 | 4.96 | 100.0 / 94.7 / 94.7 | 2.48 | +26.3 to +42.1 |
| `accessibility` | 42.1 / 52.6 / 52.6 | 4.96 | 78.9 / 84.2 / 94.7 | 6.56 | +31.6 to +42.1 |

SD is the population standard deviation of the per-repetition pass rates. Every paired repetition in every set favored the with-skill condition.

## What the numbers support

Under this host, model, reasoning effort, runner, prompt set, and three-repetition protocol, explicit use of the skill raised the assertion pass rate on every completed set, from 49.1–72.1% to 86.0–96.5%. The gain comes from corrected premises (btop's refresh interval, lazygit's redo key), facts the baseline didn't volunteer (raw mode and flow control, Bubble Tea's missing screen-reader support), and terminal cleanup rules that no framework enforces. At low reasoning effort, the with-skill answers still skip some details that the skill states and the transcript shows were read.

These results don't establish a population-level effect and don't transfer to other models, reasoning efforts, or hosts. They also say nothing about whether the skill activates on its own: every with-skill prompt named the skill explicitly. [#21](https://github.com/gfargo/tui-design-skill/issues/21) tracks implicit triggering.

## Limitations

- **Cross-family grader:** Claude Opus 5.5 graded these Codex answers. The grader never saw the condition, so any preference for Claude-style answers affects both conditions, but it may lower Codex's absolute scores.
- **Low effort:** the model ran at its lowest reasoning effort, by choice. Higher effort may change both conditions.
- **Rubric conflict:** `lazygit-config-format` assertion 4 asks the answer to choose a config format from the app's own needs, but the prompt asks to mirror lazygit's conventions, and the skill's *Configuration formats* list never states that rule. Every trial on both hosts and in both conditions failed it. The rubric is left unchanged here so the recorded eval-set hash stays valid.

## Evidence bundles

Each directory holds the run manifest, prompts, responses, stderr with the Codex transcript, grading prompt, grades with a note for every assertion, and summary:

- [`v180-v173-correction-codex-baseline-r3/`](v180-v173-correction-codex-baseline-r3/) and [`v180-v173-correction-codex-with-skill-r3/`](v180-v173-correction-codex-with-skill-r3/)
- [`v180-v171-correction-codex-baseline-r3/`](v180-v171-correction-codex-baseline-r3/) and [`v180-v171-correction-codex-with-skill-r3/`](v180-v171-correction-codex-with-skill-r3/)
- [`v180-terminal-modes-codex-baseline-r3/`](v180-terminal-modes-codex-baseline-r3/) and [`v180-terminal-modes-codex-with-skill-r3/`](v180-terminal-modes-codex-with-skill-r3/)
- [`v180-accessibility-codex-baseline-r3/`](v180-accessibility-codex-baseline-r3/) and [`v180-accessibility-codex-with-skill-r3/`](v180-accessibility-codex-with-skill-r3/)
- [`v180-l10n-environments-codex-baseline-r3/`](v180-l10n-environments-codex-baseline-r3/); the with-skill bundle follows the rerun.
