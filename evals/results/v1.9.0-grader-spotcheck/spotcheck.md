# Grader spot-check

A deterministic 15% sample of trials (seed 79) from 40 bundles, re-graded by OpenAI `gpt-6.1-sol` with each bundle's own grading prompt, compared with the original claude-opus-5-5 grades.

- **Assertions compared:** 612
- **Agreement:** 576/612 (94.1%)
- **Cohen's kappa:** 0.828
- **Pass rate:** Claude grader 80.7%, Codex grader 75.8%

## Pass rate by answering provider and condition

| Answers from | Condition | Assertions | Claude grader | Codex grader |
|---|---|---:|---:|---:|
| Anthropic | baseline | 150 | 72.0% | 64.7% |
| Anthropic | with-skill | 152 | 98.7% | 97.4% |
| OpenAI | baseline | 155 | 59.4% | 55.5% |
| OpenAI | with-skill | 155 | 92.9% | 85.8% |

## Per bundle

| Bundle | Trials | Assertions | Agreement | Kappa |
|---|---:|---:|---:|---:|
| `v190-cli-claude-baseline-r3` | 5 | 21 | 95.2% | 0.897 |
| `v190-cli-claude-with-skill-r3` | 5 | 20 | 100.0% | n/a |
| `v190-cli-codex-baseline-r3` | 5 | 21 | 100.0% | 1.000 |
| `v190-cli-codex-with-skill-r3` | 5 | 21 | 95.2% | 0.859 |
| `v190-content-claude-baseline-r3` | 3 | 13 | 76.9% | 0.519 |
| `v190-content-claude-with-skill-r3` | 3 | 13 | 100.0% | n/a |
| `v190-content-codex-baseline-r3` | 3 | 13 | 92.3% | 0.843 |
| `v190-content-codex-with-skill-r3` | 3 | 15 | 100.0% | n/a |
| `v190-design-review-claude-baseline-r3` | 2 | 9 | 100.0% | n/a |
| `v190-design-review-claude-with-skill-r3` | 2 | 8 | 100.0% | n/a |
| `v190-design-review-codex-baseline-r3` | 2 | 10 | 100.0% | 1.000 |
| `v190-design-review-codex-with-skill-r3` | 2 | 9 | 100.0% | n/a |
| `v190-ecosystem-claude-baseline-r3` | 8 | 29 | 86.2% | 0.701 |
| `v190-ecosystem-claude-with-skill-r3` | 8 | 32 | 96.9% | 0.000 |
| `v190-ecosystem-codex-baseline-r3` | 8 | 31 | 90.3% | 0.712 |
| `v190-ecosystem-codex-with-skill-r3` | 8 | 32 | 96.9% | 0.784 |
| `v190-interaction-claude-baseline-r3` | 5 | 21 | 100.0% | 1.000 |
| `v190-interaction-claude-with-skill-r3` | 5 | 22 | 100.0% | 1.000 |
| `v190-interaction-codex-baseline-r3` | 5 | 23 | 87.0% | 0.725 |
| `v190-interaction-codex-with-skill-r3` | 5 | 21 | 85.7% | 0.000 |
| `v190-routing-claude-baseline-r3` | 2 | 7 | 71.4% | 0.300 |
| `v190-routing-claude-with-skill-r3` | 2 | 6 | 100.0% | n/a |
| `v190-routing-codex-baseline-r3` | 2 | 7 | 85.7% | -0.000 |
| `v190-routing-codex-with-skill-r3` | 2 | 7 | 100.0% | 1.000 |
| `v190-structural-claude-baseline-r3` | 2 | 9 | 100.0% | 1.000 |
| `v190-structural-claude-with-skill-r3` | 2 | 9 | 88.9% | 0.000 |
| `v190-structural-codex-baseline-r3` | 2 | 9 | 88.9% | 0.727 |
| `v190-structural-codex-with-skill-r3` | 2 | 10 | 100.0% | n/a |
| `v190-tier2-claude-baseline-r3` | 3 | 15 | 100.0% | 1.000 |
| `v190-tier2-claude-with-skill-r3` | 3 | 15 | 100.0% | n/a |
| `v190-tier2-codex-baseline-r3` | 3 | 15 | 100.0% | 1.000 |
| `v190-tier2-codex-with-skill-r3` | 3 | 15 | 93.3% | 0.634 |
| `v190-tier3-claude-baseline-r3` | 2 | 10 | 100.0% | 1.000 |
| `v190-tier3-claude-with-skill-r3` | 2 | 10 | 100.0% | n/a |
| `v190-tier3-codex-baseline-r3` | 2 | 10 | 90.0% | 0.783 |
| `v190-tier3-codex-with-skill-r3` | 2 | 10 | 90.0% | 0.737 |
| `v190-v174-claude-baseline-r3` | 5 | 16 | 81.2% | 0.636 |
| `v190-v174-claude-with-skill-r3` | 5 | 17 | 100.0% | n/a |
| `v190-v174-codex-baseline-r3` | 5 | 16 | 100.0% | 1.000 |
| `v190-v174-codex-with-skill-r3` | 5 | 15 | 73.3% | 0.250 |

## Disagreements (36)

- `json-errors-r3` in `v190-cli-claude-baseline-r3`, assertion 4: Claude **pass**, Codex **fail**. Says to add fields but never remove, rename, or retype them, and to ignore unknown fields on the consumer side
- `exit-code-scheme-r2` in `v190-cli-codex-with-skill-r3`, assertion 4: Claude **pass**, Codex **fail**. Notes the exit status is 8 bits, so computed codes must be clamped (exit(256) is success)
- `status-message-timing-r1` in `v190-content-claude-baseline-r3`, assertion 1: Claude **pass**, Codex **fail**. Says success and info messages fade after about 3-5 seconds
- `status-message-timing-r1` in `v190-content-claude-baseline-r3`, assertion 4: Claude **pass**, Codex **fail**. Leads messages with a symbol or label word so the kind survives NO_COLOR
- `status-message-timing-r3` in `v190-content-claude-baseline-r3`, assertion 4: Claude **pass**, Codex **fail**. Leads messages with a symbol or label word so the kind survives NO_COLOR
- `status-message-timing-r1` in `v190-content-codex-baseline-r3`, assertion 1: Claude **pass**, Codex **fail**. Says success and info messages fade after about 3-5 seconds
- `ratatui-tui-logger-crossterm-feature-r1` in `v190-ecosystem-claude-baseline-r3`, assertion 1: Claude **pass**, Codex **fail**. Says it is not required: tui-logger depends on ratatui without default features, so the widget works with whatever backend the app's own ratatui enables
- `ratatui-tui-logger-crossterm-feature-r1` in `v190-ecosystem-claude-baseline-r3`, assertion 2: Claude **pass**, Codex **fail**. Says the crossterm and termion features of tui-logger only gate its bundled demo example (and forward to ratatui's backend feature)
- `ink-virtualize-long-list-r2` in `v190-ecosystem-claude-baseline-r3`, assertion 1: Claude **pass**, Codex **fail**. Explains that contentOffsetY (with overflow hidden) only shifts and clips the children: Yoga still lays out, and Ink still paints, every child, so cost scales with the full list
- `ink-virtualize-long-list-r2` in `v190-ecosystem-claude-baseline-r3`, assertion 3: Claude **pass**, Codex **fail**. Makes each row exactly one line, using <Text wrap="truncate-end"> (inside a fixed-width Box per cell), because the slice math assumes one row per line and the default wrap grows the row
- `ink-virtualize-long-list-r2` in `v190-ecosystem-claude-with-skill-r3`, assertion 3: Claude **pass**, Codex **fail**. Makes each row exactly one line, using <Text wrap="truncate-end"> (inside a fixed-width Box per cell), because the slice math assumes one row per line and the default wrap grows the row
- `ink-virtualize-long-list-r1` in `v190-ecosystem-codex-baseline-r3`, assertion 3: Claude **pass**, Codex **fail**. Makes each row exactly one line, using <Text wrap="truncate-end"> (inside a fixed-width Box per cell), because the slice math assumes one row per line and the default wrap grows the row
- `ink-virtualize-long-list-r3` in `v190-ecosystem-codex-baseline-r3`, assertion 1: Claude **pass**, Codex **fail**. Explains that contentOffsetY (with overflow hidden) only shifts and clips the children: Yoga still lays out, and Ink still paints, every child, so cost scales with the full list
- `ink-virtualize-long-list-r3` in `v190-ecosystem-codex-baseline-r3`, assertion 3: Claude **pass**, Codex **fail**. Makes each row exactly one line, using <Text wrap="truncate-end"> (inside a fixed-width Box per cell), because the slice math assumes one row per line and the default wrap grows the row
- `ratatui-tui-logger-crossterm-feature-r1` in `v190-ecosystem-codex-with-skill-r3`, assertion 2: Claude **pass**, Codex **fail**. Says the crossterm and termion features of tui-logger only gate its bundled demo example (and forward to ratatui's backend feature)
- `selection-stability-r1` in `v190-interaction-codex-baseline-r3`, assertion 1: Claude **pass**, Codex **fail**. Tracks the selection by a stable ID rather than a row index and re-resolves it after refresh, sort, and filter
- `tree-keys-r2` in `v190-interaction-codex-baseline-r3`, assertion 2: Claude **pass**, Codex **fail**. Shows a per-node loading spinner for lazily loaded children
- `mouse-default-r2` in `v190-interaction-codex-baseline-r3`, assertion 1: Claude **pass**, Codex **fail**. Enables modes 1000, 1002, and 1006 for a full-screen app with click targets, not 1003 unless hover effects need it
- `selection-stability-r3` in `v190-interaction-codex-with-skill-r3`, assertion 5: Claude **pass**, Codex **fail**. Offers a freeze or pause key shown in the footer, with a PAUSED marker and a count of pending changes
- `tree-keys-r1` in `v190-interaction-codex-with-skill-r3`, assertion 2: Claude **pass**, Codex **fail**. Shows a per-node loading spinner for lazily loaded children
- `tree-keys-r2` in `v190-interaction-codex-with-skill-r3`, assertion 2: Claude **pass**, Codex **fail**. Shows a per-node loading spinner for lazily loaded children
- `shift-enter-missing-r1` in `v190-routing-claude-baseline-r3`, assertion 2: Claude **pass**, Codex **fail**. Notes tmux needs the extended-keys option, which is off by default
- `shift-enter-missing-r1` in `v190-routing-claude-baseline-r3`, assertion 3: Claude **fail**, Codex **pass**. Falls back to Alt+Enter or Ctrl+J for inserting a newline and tells users the key
- `shift-enter-missing-r2` in `v190-routing-codex-baseline-r3`, assertion 3: Claude **fail**, Codex **pass**. Falls back to Alt+Enter or Ctrl+J for inserting a newline and tells users the key
- `2-r3` in `v190-structural-claude-with-skill-r3`, assertion 4: Claude **pass**, Codex **fail**. Keeps git/subprocess work outside Update and returns results through a tea.Cmd or message
- `1-r1` in `v190-structural-codex-baseline-r3`, assertion 2: Claude **pass**, Codex **fail**. Counts the duplicate readiness signals and recognizes that a marker on every row marks nothing
- `3-r3` in `v190-tier2-codex-with-skill-r3`, assertion 4: Claude **pass**, Codex **fail**. Recommends reproducing in ink-testing-library (render + lastFrame/frames + stdin.write) to isolate the state-update bug
- `3-r2` in `v190-tier3-codex-baseline-r3`, assertion 5: Claude **fail**, Codex **pass**. Names at least one plausible Ink-specific cost sink (unmemoized re-renders, <Static> misuse, or an always-animating component like a spinner) rather than only generic React advice
- `1-r1` in `v190-tier3-codex-with-skill-r3`, assertion 3: Claude **pass**, Codex **fail**. Addresses the headless/CI gap honestly — keychains depend on a running Secret Service/D-Bus daemon on Linux, so an explicit plaintext fallback is needed, not a silent failure
- `cjs-require-esm-r2` in `v190-v174-claude-baseline-r3`, assertion 1: Claude **pass**, Codex **fail**. Says Node 22.12 and later (and 20.19) can require() synchronous ES modules, so ESM-only packages such as chalk and commander no longer force old pins
- `cjs-require-esm-r3` in `v190-v174-claude-baseline-r3`, assertion 1: Claude **pass**, Codex **fail**. Says Node 22.12 and later (and 20.19) can require() synchronous ES modules, so ESM-only packages such as chalk and commander no longer force old pins
- `cjs-require-esm-r3` in `v190-v174-claude-baseline-r3`, assertion 2: Claude **pass**, Codex **fail**. Says Ink cannot be loaded with require() because its dependency graph uses top-level await, which fails with ERR_REQUIRE_ASYNC_MODULE
- `cjs-require-esm-r1` in `v190-v174-codex-with-skill-r3`, assertion 1: Claude **pass**, Codex **fail**. Says Node 22.12 and later (and 20.19) can require() synchronous ES modules, so ESM-only packages such as chalk and commander no longer force old pins
- `cjs-require-esm-r3` in `v190-v174-codex-with-skill-r3`, assertion 1: Claude **pass**, Codex **fail**. Says Node 22.12 and later (and 20.19) can require() synchronous ES modules, so ESM-only packages such as chalk and commander no longer force old pins
- `typer-vendored-click-r3` in `v190-v174-codex-with-skill-r3`, assertion 1: Claude **pass**, Codex **fail**. Says Typer 0.26 and later vendor Click instead of depending on it, so Click plug-ins and extracting the Click app are no longer supported
- `typer-vendored-click-r3` in `v190-v174-codex-with-skill-r3`, assertion 2: Claude **pass**, Codex **fail**. Says Trogon breaks with Typer 0.26 or later and is unmaintained
