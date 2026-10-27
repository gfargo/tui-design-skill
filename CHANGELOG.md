# Changelog

All notable changes to the `tui-design` skill are documented here. The format is loosely based on [Keep a Changelog](https://keepachangelog.com/), and the project follows semantic versioning.

## [Unreleased]

### Added
- **Layout wireframes and States ([#73](https://github.com/gfargo/tui-design-skill/issues/73)):** `visual-patterns.md` now shows the design instead of only describing it.
  - *The seven canonical layouts* is a decision table (use when, avoid when, 60-column fallback, exemplars) plus an ASCII thumbnail of each layout wide and at its 60-column fallback. The long per-layout prose became short notes.
  - *Responsive design* adds one app at 120, 80, and 60 columns with default pane ratios: sidebar 20–30% clamped to 20–40 columns, list at least 30, and the detail pane folding away first.
  - A new *States* section covers initial, loading, empty, partial, success, error, stale, and too small, each with a sketch and a rule. It replaces the empty, loading, and disconnected bullets that sat under *Progress indicators*.
  - Concrete defaults replace vague wording: info messages fade after 3–5 seconds while errors stay until dismissed and then go to a message log; footer hints are shown at 80 and 40 columns, most frequent first and `?` last; one blank row between groups, 1-cell padding, a 2-cell column gutter, and modals at most 60–80% wide; table status columns are left-aligned; a command palette from about 20 actions; and `/` filters lists but searches documents and logs.
  - *The clutter audit* gains a before/after example with the counts it would report.
  - `SKILL.md` tells the agent to include an ASCII sketch at the floor size in design answers.
  - `evals/v190-content-evals.json` adds six rubric cases for these behaviors (rubric-only; later v1.9.0 issues extend it).
- **Interaction gaps ([#74](https://github.com/gfargo/tui-design-skill/issues/74)):** `interaction-patterns.md` and `visual-patterns.md` cover the problems that no reference addressed, each with one owning section and a concrete default.
  - *Esc, q, and Ctrl+C*: a quit ladder (cancel, close overlay, clear filter, go back, nothing at the root), `q` backing out of nested views, Ctrl+C cancelling first, and a quit confirmation only when quitting loses work.
  - *Scrolling and position*, *Live data* (selection by stable ID, nearest neighbor on removal, a freeze key), and *Logs and streams* (follow mode, `▾ 37 new`, `G`/`F`, wrap toggle, ring buffer).
  - *Text input*: readline aliases, history, ghost text and the Tab collision, and multi-line submit with `Alt+Enter` or `Ctrl+J` when Shift+Enter is unavailable. *Tree views*, and a mouse default of modes 1000 + 1002 + 1006 with an off switch.
  - In `visual-patterns.md`: emoji width in aligned columns, diff views, modal geometry, and toasts with a message log.
  - `SKILL.md` routing rows name the new topics, and `evals/v190-interaction-evals.json` adds eleven rubric cases (rubric-only).

### Changed
- **Terminal protocols reference ([#72](https://github.com/gfargo/tui-design-skill/issues/72)):** the terminal modes, escape sequences, and environment matrix moved out of `interaction-patterns.md` into a new `references/terminal-protocols.md`, so design questions about keys, focus, and confirmation no longer load DECRQM and OSC details. The new file keeps the framework-defaults table, turns the per-mode bullets into one table (Mode | Enable / disable | Detect | Support floor | Gotcha), and trims per-terminal timeout and version trivia. `interaction-patterns.md` shrinks 41% by characters (40,919 to 23,934) and keeps a short *Keys the environment steals* table because it constrains keymap design; total reference size does not grow.
  - `SKILL.md` gains a routing row for escape sequences, terminal modes, multiplexer, SSH, and Windows behavior, clipboard, links, notifications, and color and theme detection.
  - The file is in `scripts/skill-files.txt`, so it ships in `tui-design.skill`, and the eight protocol-link inventory entries point at it.
- **Reference trim ([#77](https://github.com/gfargo/tui-design-skill/issues/77)):** the references drop from 4,461 to 3,680 lines (−781, −17.5%) and from 40,027 to 36,356 words (−3,671, −9.2%), freeing room for the 1.9 additions without growing the skill. Cuts are history, anecdotes, production-user lists, and prose repeated across files; no rule or v1.8.2 correction was removed.
  - **Exemplar apps:** neovim, Glow, and yt-dlp/aria2 are gone; Harlequin and Toolong are one entry, lazydocker and gitui are folded into lazygit, bottom into btop, and ranger/lf/nnn/broot into yazi. Every entry now has Layout / Copy this / Lesson / Cite when, and the intro is an app → lesson → when-to-cite table.
  - **Interaction patterns:** *Keybinding philosophies* and *Modal vs modeless* are one section with a decision rule, the named patterns are shortened to the fzf recipe plus a short paragraph each, and the raw-mode flow-control fact is stated once.
  - **Visual patterns:** *Visual hierarchy* is a subsection of *Typography*, the border, density, theming, and Nerd Fonts lists are shorter, and the focus rule points to `interaction-patterns.md` → *Focus indicators* instead of repeating it.
  - **CLI basics:** the environment-variable table is one sentence, and the final checklist is ten review questions that point to the owning sections.
  - **Ecosystems:** TypeScript has one runtime-floors table, its stack recommendations are a table, and its two "Pitfalls" headings are renamed *Ink pitfalls* and *Cross-library pitfalls*. Framework subsections in the Python and TypeScript references moved from `##` to `###`. Go and Rust drop release history, production-user lists, and repeated companion-crate text.

## [1.8.2] — 2026-10-26

Correctness patch for the 1.8 line from the October 2026 reference audit (#68–#71): wrong or missing facts in the ecosystem, CLI, and pattern references, and guidance that contradicted itself.

### Fixed
- **Go and Rust ([#68](https://github.com/gfargo/tui-design-skill/issues/68)):**
  - Lipgloss v2 `Width`/`Height` include border and padding, so v1 layout math comes out 2 cells too narrow.
  - A v1 → v2 cheat sheet gathers the Bubbles setters (`SetWidth`, `viewport.WithWidth`), `DefaultKeyMap()`, `isDark` style constructors, and `New`.
  - Global keys such as `q` must not fire while a list filter is active, and Bubble Tea never binds Ctrl+Z for you.
  - `tea.View.ProgramStatus` is not cleared on exit, and `gh` is on Glamour v2.
  - `ratatui::restore()` disables only raw mode and the alternate screen, so the Ratatui section shows teardown for mouse capture, bracketed paste, and Kitty keyboard flags, on normal exit, on panic, and across an editor handoff.
  - The canonical example uses `ratatui::run()`, and Ratatui has no suspend support, so a Unix suspend path is shown.
  - Crossterm already drops color under `NO_COLOR`, the Tokio loop redraws only after a change, and the sixth template is `hello-world`.
- **Python and TypeScript ([#69](https://github.com/gfargo/tui-design-skill/issues/69)):**
  - Textual binds Ctrl+C to a help toast and Ctrl+Q to quit; the rebinding is `Binding("ctrl+c", "quit", priority=True)`.
  - `call_from_thread` exists only on `App`, so widgets use `self.app.call_from_thread`.
  - Textual captures `print()` and the real hazards are `sys.__stdout__`, fd 1, and child processes.
  - `set_reactive` is a method, and the snapshot-suite pin is `pytest>=8.4,<9`.
  - Clack and Inquirer exit 130 on cancel, with Inquirer's `ExitPromptError` caught.
  - Prompt libraries and Ink write to stdout by default, so the redirect to stderr is shown.
  - Ink rewrites the whole output unless `incrementalRendering` is set.
  - OpenTUI 0.7 broke custom renderables and removed the hit grid.
  - `<Newline>` goes inside `<Text>`, borders accept a `BoxStyle` object, `useAnimation` resets rather than pauses, Node dates are gone, and cac needs 7.0.1 or later.
- **CLI and exemplars ([#70](https://github.com/gfargo/tui-design-skill/issues/70)):**
  - A Go program exits on SIGPIPE by default, and `gh` compiles its update checker in only under the `updateable` tag.
  - `gh auth login` has no `--no-browser`, and `GH_PROMPT_DISABLED` is the prompt-off convention.
  - `gh` groups commands, not flags; examples lead the help text; yargs and picocli do not generate every shell's completions.
  - starship installs a `preexec` hook, `.NET` has not adopted `DO_NOT_TRACK`, the config order is cited from clig.dev, and POSIX.1-2024 is current.
  - create-astro uses `@astrojs/cli-kit`, atuin is inline with an `inline_height` cap, and the ranger heading lists Python, Go, C, and Rust.
  - One error-format rule: a plain `error:` or `warning:` prefix and no log-level labels. The fix command comes last, `sysexits` is adopted whole or not at all, and cancelling a prompt exits 130.
- **Visual and interaction patterns ([#71](https://github.com/gfargo/tui-design-skill/issues/71)):**
  - Recommended glyphs are narrow (`▸ ▾ ▴ ⋅ ◉ ◦ ∙`). East Asian Ambiguous glyphs (block elements, box drawing, `▶ ▼ ▲ ○ …`) carry a stated risk and an ASCII fallback, including `[#####     ]` for progress bars.
  - Contradictions resolved to one rule each:
    - Focus must survive `NO_COLOR`: border weight, then reverse video, then a title marker, with color as reinforcement.
    - Status messages lead with a symbol, and errors stay until dismissed.
    - A state gets at most one color cue plus one non-color cue.
    - Multi-select uses Space, or Tab in type-to-filter pickers.
    - The Ctrl+P caveat is stated once.
    - Breakpoints are 120+, 80–119, 60–79, and below minimum.
    - The cursor is hidden only while painting and re-shown on the focused field.
  - tmux 3.6 added mode-2031 theme reports, and DECRQSS can query the cursor shape.
  - Mode 1000 already reports releases, and the kitty keyboard list now includes iTerm2, xterm.js, Rio, and Warp.
  - no-color.org dates from 2017, and the unsupported statistics are removed.

### Release engineering
- **Sample checks:** six new `check=` samples cover Lipgloss block size, the Bubbles v2 API, list-filter key routing, Ratatui extra-mode teardown, Ratatui suspend, and the Textual Ctrl+C rebinding. The Rust `rust/run` sample is replaced by the canonical `ratatui::run()` example. The Rust harness adds `signal-hook`.
- `scripts/reference-inventory.json` gains 24 entries: Lipgloss v2.0.6 block sizing, OpenTUI 0.7.0, cac 7.0.1, and source links for the new claims. Two links now point at immutable refs.

### Evaluation
- `evals/v182-correction-evals.json` covers the corrected facts with 39 rubric cases, including Lipgloss sizing, Bubbles v2, filter keys, Ratatui teardown, Textual Ctrl+C, `call_from_thread`, prompt-cancel exit codes, Go SIGPIPE, the error-format rule, ambiguous-width glyphs, and focus under `NO_COLOR`. It is rubric-only: no run is recorded.

## [1.8.1] — 2026-10-13

Evidence release for the 1.8 line. It records baseline and with-skill runs on Claude Code and Codex, measures implicit triggering on both hosts, freezes eval-schema growth, and fixes one guidance gap the runs exposed.

### Fixed
- **Configuration formats:** `visual-patterns.md` → *Configuration formats* now says that no format is the TUI standard, and that matching a tool your users already configure, such as lazygit, is a good reason to use its format. The guidance listed formats but never stated that rule, which the v1.7.1 rubric expected.

### Release engineering
- **Frozen schema requirements:**
  - `scripts/eval_harness.py` names each schema version's evidence requirements in one `SCHEMA_REQUIREMENTS` table.
  - Validation checks `requires(version, name)` instead of comparing version numbers.
  - A test pins the published sets.
  - `evals/README.md` → *When a new schema version is justified* records the policy: new versions need a new evidence requirement, bump only the changed artifact, and share `$defs`.
  - Behavior for existing bundles is unchanged.

### Evaluation
- **Two-host evidence:** `evals/results/v1.8.0-claude-comparison/` and `evals/results/v1.8.0-codex-comparison/` record baseline and with-skill runs of the v1.7.1, v1.7.3, and three v1.8.0 eval sets, plus the v1.7 lifecycle set on Claude, with three repetitions per case and a report for each host. With the skill, Claude Code (`claude-opus-5-5`) and the Codex CLI (`gpt-6.1-sol`, low effort) both scored higher on every set.
- **Isolated runners and a blind grader:** `scripts/runners/` adds Claude Code and Codex runners that switch off installed skills, plugins, MCP servers, user settings, and web search, and a Claude grader that never sees the condition and records a note for every assertion. `evals/README.md` → *Runners and grader* documents them.
- **Rubric-only labels:** the eval sets without a recorded run (`evals.json`, `build-evals.json`, the tier-2 and tier-3 sets, v1.5.1, v1.6.0, and v1.7.4) say so in their notes.
- **Trigger calibration:** `evals/results/v1.8.0-trigger-calibration/` measures implicit activation of the v1.8.0 description on Claude Code and Codex with 42 prompts, three repetitions each, using `scripts/runners/trigger_probe.py` and `evals/v180-trigger-evals.json`. Positive prompts triggered 57/57 on both hosts, adjacent prompts 0/45 on Claude and 1/45 on Codex, and unrelated prompts 0/9, so the description is unchanged. The hosts differ on ambiguous terminal-configuration prompts, which Codex usually loads the skill for and Claude usually doesn't.
- **lazygit-config-format rubric:** the fourth assertion asked for a format chosen from the app's own needs, which conflicted with a prompt that asks to mirror lazygit; it failed in all 12 v1.8.0 trials on both hosts. It now checks that the answer doesn't present one format as the TUI standard and ties its recommendation to matching lazygit or to the app's needs. The recorded bundles keep the original eval-set hash.

## [1.8.0] — 2026-10-12

Content and tooling release that completes most of the September 2026 audit roadmap. It adds accessibility, terminal-mode, localization, and terminal-environment guidance; gives each topic one owning reference; compiles and tests the reference code samples in CI; and hardens release validation and reference-freshness checks.

### Added
- **Accessibility section:** `visual-patterns.md` → *Accessibility* gathers what was scattered across five files. It explains what screen readers hear in a terminal (every repaint is read as new text) and gives rules that work: append instead of repaint, status in words, flattened tables, numbered choices, labelled lines, errors written to be spoken, and a cursor kept on the focus. It also defines the plain-mode contract, compares framework support, and covers reduced motion. `SKILL.md`'s routing row and `--no-tui` bullet point to it; the ecosystem references keep their API specifics and link to it.
- **Terminal modes and protocols:** `interaction-patterns.md` gains a section on the modes a full-screen app turns on and must turn off: bracketed paste, the kitty keyboard protocol and `modifyOtherKeys`, mouse and focus reporting, synchronized output, cursor shape, window title, OSC 9;4 progress, OSC 133 prompt marks, grapheme clusters, color-depth detection, OSC 11 background queries, mode 2031 theme notifications, and tmux and SSH behavior. A table shows which modes Bubble Tea, crossterm/Ratatui, Textual, and Ink enable by default, and each item gives a safe default, a fallback, and what to restore on exit.
- **Localization:** `visual-patterns.md` → *Localization*:
  - Translation growth: short labels grow most, per IBM's and Microsoft's figures.
  - Pseudo-locale testing at the 60-column floor.
  - Right-to-left text: which terminals reorder it, and what a full-screen app should do.
  - Ambiguous-width characters, which include nearly all box drawing and common markers.
  - Locale-aware human output with locale-independent machine output.
  - POSIX locale precedence.
- **Terminal environments:** *Terminal modes and protocols* → *Multiplexers and SSH* is now a matrix of what breaks, how to detect it, and the fallback. It covers tmux (prefix, `escape-time`, 3.8's default mouse bindings), GNU screen (prefix, truecolor off by default, dropped OSC, flow control), Zellij (captured Ctrl and Alt keys, Unlock-First), SSH, Windows (no job-control signals, VT history, `WT_SESSION`), and CI.

### Changed
- **One owner per topic:** filter behavior, footer-hint content, cursor-shape mode indication, secrets handling, and startup budgets for summoned tools each have one full treatment, and the other copies are one-line pointers. The framework APIs for inline versus alternate-screen mode and for dynamic Huh and Textual forms moved from the pattern references into the ecosystem references. References shrink from 4,287 to 4,271 lines.
- **Trimmed hedging and repetition:**
  - The stale-data and timeout paragraphs in `visual-patterns.md` and the `DO_NOT_TRACK` history in `cli-basics.md` became short rules.
  - Rust's profiling paragraph was halved.
  - Textual's testing claim, TCSS live reload, and Cobra's `PreRun` warning are each stated once, and Textual's `add_rows` correction moved to *Pitfalls*.
  - Ratatui's layout-cache advice is one consistent sentence.
  - "argparse" now means only Python's module; elsewhere the text says "argument parsing".
  - References drop from 37,015 to 36,641 words.

### Fixed
- **Unconfirmed claims resolved:**
  - Huh's standalone `form.Run()` never requests the background color, so it always renders the light variant. The Go reference now shows how to detect the background first and pin the variant, and notes that Huh's upgrade-guide `WithTheme(huh.ThemeCharm(isDark))` example doesn't compile against v2.0.3.
  - The Termwiz line no longer implies that Ratatui's termwiz backend exposes images; `ratatui-image` is the path.
  - urwid's release dates are exact.
  - The gitui snapshot PRs (#2411 merged then reverted, #2813 merged 2026-04-07), crush's test files, and Ratatui #1227 were checked and kept.
- **Accessibility pointers:** the *Accessibility* framework table points at the TypeScript reference's real *Strengths and weaknesses* heading, and the focus rule asks for one non-color cue combined as *Focus indicators* describes.
- **Accessibility facts:** `textual serve` is no longer called an accessibility path; its xterm.js canvas runs with screen-reader mode off, and Textual has no screen-reader support. Huh's accessible mode is described field by field, including that it switches on by itself only for `TERM=dumb`. Ink's screen-reader renderer is opt-in and still rewrites the live region on every change. Ratatui's missing accessibility layer is listed as a pitfall.
- **TypeScript guidance:** the simple non-interactive CLI stack (commander, picocolors, ora) installs 19 packages and about 0.9 MB, not "~30 KB".

### Release engineering
- **Wider freshness coverage:**
  - `check-reference-freshness.py` gains an `engine_floor` kind that reads `engines` and peer ranges from the latest npm manifest, with offline fixture tests.
  - The inventory now tracks Huh, Bubbles, urfave/cli, Crossterm, tui-logger, InquirerPy, ink-testing-library, commander, chalk, neo-blessed, the Ink, commander, chalk, and OpenTUI engine floors, and source links for gh's `go.mod`, Ratatui's Crossterm features, Ink's aria and `suspendTerminal` releases, and Node's `styleText` and `parseArgs` docs.
  - 35 entries in total, all current.
- **Release validation hardening:**
  - The packaged-file allowlist lives in `scripts/skill-files.txt`, which the packager, the validator, and the packaging tests all read. It previously appeared in five places.
  - The validator parses frontmatter keys with an anchored pattern, so a folded (`>-`) description passes.
  - The validator requires the `plugin.json` and `marketplace.json` descriptions to match each other and to start with `SKILL.md`'s first description sentence.
  - The validator requires a compare link for every changelog version and an `[Unreleased]` link from the current version.
  - New tests cover the validator's failure modes, schema-v5 run, grades, and summary conformance (with `jsonschema`), and `validate-evidence.sh`. The evidence script now reports a recorded commit that is missing from the repository by name.
  - The validate workflow runs on Python 3.9 and 3.14.
- `scripts/reference-inventory.json` adds source links for the kitty keyboard protocol, the synchronized-output and color-palette-update specs, ConEmu's and Windows Terminal's OSC 9;4 docs, and the tmux 3.8 manual.

### Evaluation
- **Honest eval provenance:**
  - `build-evals.json`'s 27/27 vs 24/27 figure is labelled an unverified historical observation, since no bundle was committed.
  - `trigger-evals.json` is labelled unverified and notes that its harness measured a slash command, not the plugin skill.
  - `tier3-content-evals.json` no longer cites briefs that aren't in the repository.
  - `v170-lifecycle-evals.json` asks for a run in the current schema.
  - `GRADER-CORRECTION.md` files record that the v1.7.0 lifecycle bundles were graded by a Codex agent despite `grader.kind: "human"`; the hashed artifacts are unchanged.
  - The pre-harness v1.6.0 report is documented as informal notes.
- `evals/v180-l10n-environments-evals.json` covers translation growth at 60 columns, a tmux prefix and Esc-delay collision, ambiguous-width borders under a Japanese locale, and locale-independent machine output.
- `evals/v180-terminal-modes-evals.json` covers multi-line paste without bracketed paste, tearing and synchronized output, Shift+Enter and the kitty keyboard protocol, background-color queries over SSH and theme notifications, and restoring the cursor shape and window title.
- `evals/v180-accessibility-evals.json` covers a Huh form made usable with a screen reader, what `--no-tui` must output, `textual serve` as an accessibility claim, and Ink's screen-reader live region.

## [1.7.4] — 2026-10-12

Correctness patch after an October 2026 freshness audit against current framework releases, plus CI that builds and tests the reference code samples so they cannot drift from real APIs.

### Fixed
- **Current releases:**
  - Ink 8.0 (October 2026) is the current major. It needs React 19.3 and accepts only numbers for `minWidth`/`maxWidth`. It types `stdout` as a generic stream, so read the width from `useWindowSize()`, and `useInput` drops unrecognized terminal sequences.
  - Bubble Tea v2.1 is current and needs Go 1.26.
  - Node 20 and Python 3.10 are end-of-life. The references now target Node 22 or 24 and Python 3.11+, and keep the Ink 6 / chalk 5 / commander 14 pins only as a bridge for Node 20.
- **Reserved keys:** `SKILL.md` no longer says to preserve flow control. It now matches the reserved-keys reference: `Ctrl+C` cancels or quits, `Ctrl+Z` suspends through the framework, and a full-screen app may bind `Ctrl+S`.
- **Go guidance:**
  - Embedding a Huh form type-asserts the `huh.Model` that `Form.Update` returns.
  - New lazy-style apps use Bubble Tea. lazygit now keeps its own gocui fork on tcell v3, so gocui is no longer recommended.
  - Always render a default palette, because `BackgroundColorMsg` may never arrive. The parent of an embedded Huh form must request the background color itself.
  - `tea.Println` prints above an inline UI, and the TUI is gated on stdout being a terminal.
  - Glamour v2, Wish's filter ordering, golden-file storage, the spinner list and tcell v3 are now described accurately, and Syncthing is credited to Kong rather than urfave/cli.
- **Rust guidance:**
  - `ratatui-textarea` replaces `tui-textarea`, which requires Ratatui 0.29.
  - Corrected descriptions of the Termina backend, the six `ratatui/templates`, the PTY layer of the official snapshot recipe, `clap_complete`, tui-logger's features and cursive's release status.
  - The profiling notes match cargo-flamegraph and samply.
- **Python guidance:**
  - Typer 0.26 vendors Click, so Click plug-ins, including Trogon, no longer work with it. Trogon is also unmaintained.
  - questionary returns `None` on `Ctrl-C`, and prompt_toolkit draws on stdout unless redirected.
  - Snapshot suites pin `pytest<9`, and async tests need pytest-asyncio.
  - Posting 3 is a Go rewrite.
  - The Textual suspend link points at an anchor that exists.
- **TypeScript guidance:**
  - CommonJS programs can `require()` chalk, commander, Clack and Inquirer on Node 20.19+/22.12+, but must load Ink with `import()`.
  - ink-testing-library input tests work on Ink 6.8–8 when they await after each write.
  - @inkjs/ui inputs are uncontrolled, and terminal-kit has no Sixel support.
  - The listr2, commander, yargs, Clack, OpenTUI and Pastel facts are current.
- **Exemplars and patterns:**
  - The AI chat case study now presents two options: inline `<Static>` history, or an alternate-screen virtualized transcript. Claude Code's fullscreen renderer and Copilot CLI use the alternate screen.
  - lazygit reloads its config on focus, k9s filters by regex, and helix and fzf enable the mouse by default.
  - OSC 9 notification text must not start with `<digits>;`.
  - delta does not read `NO_COLOR`, and `FORCE_COLOR` precedence differs by runtime.
  - commander has no built-in shell completions.
  - `XDG_STATE_HOME` holds state that persists between restarts.
  - starship is described by its per-module time budgets.
- **Demo-recording route:** screenshots and demo GIFs no longer route only to the separate `vhs-cli-demos` skill, which ships only with the `gfargo/skills` marketplace and was missing from every other install path. The skill uses `vhs-cli-demos` when it is installed and otherwise falls back to `cli-basics.md` → *Demo recordings*: a short VHS guide to tapes, `Set Columns`/`Set Rows` sizing, `Wait`, `Require`, and lossless GIF optimization. README → *Install* says where to get `vhs-cli-demos`.
- **Rust samples:** the canonical app quits on Ctrl+C and Esc as well as `q`, because raw mode delivers Ctrl+C as a key event; the Tokio loop stops when the input reader ends instead of ticking forever with no way to quit; the Cursive sample builds with `cursive::default()`; the Elm sketch compiles.
- **Python samples:** the canonical Textual app uses inline `CSS` instead of a `hello.tcss` that was never supplied; the Pilot test carries `@pytest.mark.asyncio` for pytest-asyncio's default strict mode; the worker sample passes `Static` to `query_one`; the modal sample has its imports; the Rich sample sends errors and progress to a stderr console; the questionary sample exits 130 on Ctrl-C instead of continuing with `None`.
- **Go samples:** standalone Lipgloss output goes through `lipgloss.Println`, which downsamples for the terminal, because v2 `Render` always emits truecolor; the teatest sample uses `colorprofile.ASCII`; the debug-log snippet checks the `tea.LogToFile` error so logs cannot land in the TUI.

### Release engineering
- `scripts/reference-inventory.json` tracks Ink 8.0.0 and Bubble Tea v2.1.0. Bubble Tea is now checked at minor precision, so a new minor release gets flagged. Source links point at the current tags and at a Textual anchor that exists.
- **Sample checks:** 48 reference code fences carry a `check=<harness>/<name>` marker and are built and tested in CI (`.github/workflows/samples.yml`) against pinned versions: `go vet` and `go test` on Bubble Tea v2.1.0, Lipgloss v2.0.6, Bubbles v2.2.1, and Huh v2.0.3; `cargo check` and `cargo test` on Ratatui 0.30.2 with Crossterm 0.29; pytest on Textual 8.2.8 and Rich 15.0.0; `tsc --strict` and vitest on Ink 8.0.0. Wrapper code lives in `tests/samples/`, outside the packaged skill, and `validate-release.sh` fails when a marked sample has no harness template.

### Evaluation
- `evals/v174-correction-evals.json` covers the corrected facts:
  - Huh embedding and Lipgloss v2 printing
  - ratatui-textarea, the Tokio `select!` reader exit and raw-mode `Ctrl+C`
  - Ink 8 floors and API changes, and CommonJS `require(esm)`
  - Typer vendoring Click
  - the AI chat rendering trade-off
  - gocui for new apps
  - pytest-textual-snapshot on pytest 9
- The v1.7.3 `ink-suspend-node20` rubric now expects answers to say Node 20 is end-of-life and to treat the Node 20 pins as a bridge. No recorded bundle uses that eval set.

## [1.7.3] — 2026-09-24

Correctness patch after a September 2026 audit that checked every code sample and version-sensitive claim against tagged upstream sources, plus release-workflow hardening.

### Fixed
- **Code samples:** the Ratatui canonical example now imports `DefaultTerminal` and Crossterm's event types; the `TestBackend` assertion matches the buffer Ratatui actually renders; the Textual reactive example declares the reactive its `compute_` method derives and no longer shadows `Widget.display`; the Pilot test targets the example app's real IDs; the ink-testing-library test tolerates the round border and awaits input; Clack's `validate` handles `undefined` and the `select` result is checked with `isCancel`; the Bubble Tea fetch command reads the response body; Huh v2 themes use `huh.ThemeFunc(huh.ThemeCharm)`.
- **Go guidance:** `gh` uses Bubble Tea, Bubbles, and Huh for its prompts; inside a running Bubble Tea program, request the background color with `tea.RequestBackgroundColor` rather than querying the terminal with `lipgloss.HasDarkBackground`; the Bubbles `table` has no built-in sorting and `tree` is listed; `help.View` requires a `help.KeyMap`.
- **Rust guidance:** `EventStream` needs Crossterm's `event-stream` feature; the Tokio loop uses a cancellable reader that is stopped before restore or child handoff; the editor handoff is one snippet that keeps both child and reentry results; import Crossterm through `ratatui::crossterm`, and enabling both version flags is not an error; color-eyre, `ratatui::restore()`, clap, and `Line::width()` details corrected.
- **Python guidance:** Textual's reactive order is validate → assign → watch → compute; `app_resume_signal` is named; Textual has shipped five majors since May 2025; `logging_redirect_tqdm` does not capture `print()`; InquirerPy is unmaintained; Rich diagnostics belong on a `Console(stderr=True)`.
- **TypeScript guidance:** `suspendTerminal` requires Ink 7.1+; aria props arrived in Ink 6.2 and screen-reader mode is still opt-in; ink-testing-library 4.0.0 predates Ink 6/7; Ink 7, chalk 6, and commander 15 require Node 22, so Node 20 deployments pin Ink 6, chalk 5, and commander 14; `node:util.parseArgs` is stable from Node 20 and `styleText` is the zero-dependency color option; OpenTUI's runtime floor, neo-blessed's status, and `sv` replacing create-svelte are stated.
- **Reserved keys:** raw mode delivers Ctrl+C, Ctrl+Z, and Ctrl+S as keypresses, so full-screen apps may bind them; the contract is to preserve cancel/quit and framework-managed suspend, and flow-control freezes only affect cooked-mode programs.
- **Exemplar facts:** lazygit pulls with `p`, pushes with `P`, and its reflog-backed `z`/`Z` undo cannot reverse pushes or working-tree changes; helix shows its mode in the status line, keeps per-mode cursor shapes and colors opt-in, uses a picker rather than a sidebar tree, and enables the mouse by default; btop's default layout and mouse support are described accurately and it has no drag-resize; bottom descends from gtop/gotop; ripgrep's smart case needs `-S`; yazi's number keys switch tabs.
- **Visual and CLI guidance:** truncate paths at the start or middle so the filename survives; `Ctrl+Tab` needs an enhanced keyboard protocol and `Ctrl+B` collides with tmux; `NO_COLOR` applies when non-empty, `FORCE_COLOR=0` forces color off, and `CLICOLOR_FORCE` is covered; the spinner delay is 100–200ms in every reference; git's default `LESS` is `FRX`; the argument-count rule is attributed to 12 Factor CLI Apps; unverifiable app specifics were softened or replaced with sourced text.
- **Plugin metadata:** `plugin.json` and `marketplace.json` descriptions match the skill's design/build/refactor/review scope and declare homepage, repository, and license.

### Release engineering
- The release workflow checks out without persisted credentials so steps that run third-party code cannot read the write token, lints `validate-evidence.sh`, and skips an identical asset instead of clobbering it when publishing re-triggers the workflow; it refuses to replace a different asset on a published release.

### Evaluation
- `evals/v173-correction-evals.json` covers the corrected facts: lazygit undo scope, raw-mode reserved keys, Huh v2 themes, Bubble Tea background detection, Ratatui async input handoff, Textual computed reactives, Node 20 pins, path truncation, and smart-case defaults.
- The v1.7.1 `reserved-ctrl-s-save` rubric now grades raw-mode behavior instead of treating flow control as a universal freeze; no recorded bundle uses that eval set.

## [1.7.2] — 2026-09-10

Release-engineering patch that makes committed evaluation evidence verifiable from any checkout or CI runner. Skill content is unchanged from 1.7.1.

### Added
- **Schema v5 portable evidence:** run manifests now record `skill_invocation_path`, the absolute skill directory embedded in every with-skill prompt, so a bundle can be revalidated from a checkout at any location instead of only from the exact path that produced it. `validate` and `score` gain `--source-root` (a clean checkout of the recorded commit to hash eval-set and skill inputs against) and `--recorded-skill-path` (the path that a schema-v2, v3, or v4 with-skill bundle embedded in its prompts). Historical bundles keep their schema versions, hashes, and rules; the committed v1.6.1 and v1.7.0 with-skill evidence validates from any machine by passing the path documented in `evals/README.md`. `scripts/validate-evidence.sh` revalidates every committed bundle against a snapshot of its recorded commit, and the validate workflow now runs it.

## [1.7.1] — 2026-09-02

Correctness patch after a three-pass fact-check of every reference claim against package registries, changelogs, and upstream sources, bundled with the schema-v4 grading-prompt integrity and reference freshness audit work merged since 1.7.0.

### Fixed
- **Python guidance:** the Rich traceback installer is `rich.traceback.install()`, not a nonexistent `rich.install()`; Poetry and Sphinx are no longer cited as Rich users (neither depends on it); the dev CLI command is `textual diagnose`.
- **Go guidance:** Cobra has generated the `completion` subcommand automatically since v1.2, so the reference no longer tells readers to add or scaffold one; `urfave/cli` now points at the v3 line; the Bubbles embedding example uses v2 signatures (`View() tea.View`, `tea.KeyPressMsg`); Wish v2 guidance uses `bubbletea.MakeOptions` instead of the removed `MakeRenderer`; `gh` is no longer cited as a Bubble Tea app; `tea.LogToFileWith` is no longer described as v2-only.
- **Config-format facts:** lazygit, lazydocker, and k9s plugins use YAML, not TOML; alacritty has used TOML since 0.13; bat, fzf, and delta do not use TOML config files; btop themes are `.theme` files. The btop case study no longer claims per-widget refresh cadences (btop has a single `update_ms`).
- **CLI guidance:** goreleaser's deprecated Homebrew key is `brews`, not `homebrew_formulas`; the AWS CLI CVE-2026-13769 example now names the three affected subcommands instead of implying `aws configure` was affected.
- **Interaction guidance:** neither vim nor helix binds `Ctrl+S` to save by default (helix uses it for `save_selection`); `Ctrl+A` is GNU screen's prefix rather than tmux's default.
- **Visual guidance:** repaired the dangling cross-reference to a removed SKILL.md section; the Braille `dots` spinner has ten frames; starship's preset is `nerd-font-symbols`.
- **Second-pass audit:** the four ecosystem references' tables of contents now use GitHub's heading-slug rules, so every in-file anchor resolves (18 were broken, including one pointing at a renamed Ratatui heading); `cli-basics.md` and `visual-patterns.md` now agree that a progress indicator waits roughly 100–200ms instead of contradicting each other; the gitui snapshot-test anecdote now states the actual cause of the revert (a dropped initial notify event in the refactored main loop, re-landed April 2026); the OSC 52 note records that Alacritty has ignored clipboard writes from unfocused windows since 0.11.
- **Third-pass audit:** tview's threading rule was backwards (a bare `Draw()` from a goroutine is safe; calling it inside an event handler deadlocks); the DO_NOT_TRACK paragraph now names real adopters (netdata, tilt, GitHub CLI) instead of Homebrew, Gatsby, Syncthing, and .NET, which all rejected it; blessed's last release was 2015, not 2017; create-astro uses its own cli-kit rather than Clack; Glow 2.0 removed the stash feature; btop has no drag-resize and opens help on `h`, `?`, or F1; k9s sorts via Shift+letter, not `<`/`>`; starship's speed story is its per-module timeouts, not an async placeholder; Posting's and Harlequin's feature lists now match their READMEs; yazi's no-Nerd-Font answer is editing `theme.toml`; unsourced download counts and startup-millisecond figures were replaced with relative language; `tui-link` is a repo, not a crate; crush's test-file count updated.
- **Eval rubric:** the `cobra-app-completion` case in `evals/v161-correction-evals.json` asserted that `cobra-cli add completion` should scaffold a completion command, which contradicts Cobra's built-in command; the rubric now grades the correct behavior. The recorded v1.6.1 run bundle keeps its original eval-set hash and validates against that snapshot.

### Added
- **Correction evals:** `evals/v171-correction-evals.json` covers the facts corrected in this release: the Rich traceback installer, lazygit and k9s config formats, Ctrl+S flow control, btop's single refresh rate, Wish v2 session options, the spinner delay contract, tview goroutine drawing, and DO_NOT_TRACK adoption.
- **Schema-v4 grading-prompt integrity:** grades now record `grading_prompt: {path, sha256}`, machine-linking `grader.prompt_sha256` to a grading-prompt file preserved inside the same evidence bundle. The harness enforces bundle containment and rejects path traversal, missing files, and digest mismatches. Schema v2 and v3 evidence remains readable and valid under their original, unchanged rules.
- **Reference freshness audit:** `scripts/check-reference-freshness.py` and `scripts/reference-inventory.json` check pinned Bubble Tea, Ratatui, Textual, and Ink version claims against their primary package registries and verify cited source links still resolve, without ever editing reference content. Ambiguous or unreachable checks report `unknown` rather than failing. `.github/workflows/reference-freshness.yml` runs the audit weekly and on demand.
- **Repeated lifecycle evidence:** the schema-v4 baseline-versus-with-skill study runs all five v1.7 lifecycle cases three times per condition with the exact release runner/model settings. The isolated baseline scored 63/75 (84%) and the with-skill condition scored 69/75 (92%), with the same +8 percentage-point difference in every repetition; the committed report preserves case-level outcomes, zero aggregate repetition variance, limitations, raw artifacts, grades, and summaries.

## [1.7.0] — 2026-08-18

Reliability release focused on framework-native terminal lifecycle boundaries and reproducible evaluation provenance.

### Added
- **Schema-v3 evaluation provenance:** new runs declare stable machine-readable schema anchors and record an exact runner version, exposed seed and temperature, plus a privacy-preserving system-prompt status or SHA-256/length pair.
- **Grader provenance:** schema-v3 grades anchor the exact grading prompt by version and SHA-256; model graders also identify their provider, model, runner version, and generation settings.
- **Contributor evidence contract:** `evals/README.md` documents privacy boundaries, reproducibility limits, run review steps, schema evolution, and the complete evidence bundle.
- **Framework lifecycle matrix:** the Go, Rust, Python, and TypeScript references now distinguish final exit, OS termination, interactive-child handoff, foreground suspension, and resume behavior using current framework-native APIs.
- **Lifecycle regression evals:** `evals/v170-lifecycle-evals.json` covers Bubble Tea editor handoff, Ratatui input-reader coordination, Textual suspension portability, Ink's resumable terminal API, and cross-framework signal boundaries.
- **Single-snapshot lifecycle evidence:** all five lifecycle cases ran once against clean commit `19e77052c3dc07ee1620e2bac8e42d74c0f82d3c` with OpenAI Codex desktop CLI `0.147.0-alpha.6.5`, exact model `gpt-5.6-terra`, and high reasoning. The human-graded schema-v3 bundle scored 25/25 and preserves the hashed grading protocol, raw prompts, answers, stderr, grades, and recomputed summary under `evals/results/v1.7.0-lifecycle-forward-test/`.

### Changed
- **Summary verification:** validation now requires grades alongside a summary and recomputes aggregate and per-case results, detecting tampered totals instead of checking only file hashes.
- **Historical compatibility:** the harness emits schema v3 while continuing to score and validate schema-v2 artifacts from v1.6.1.
- **Terminal handoff contract:** the procedural core now makes temporary release/reentry a separate boundary from final unmount, including stale-state refresh and full redraw requirements.

## [1.6.1] — 2026-08-18

Correctness and release-integrity patch following an adversarial review of the complete v1.6.0 source, artifact, evaluation evidence, and framework guidance.

### Fixed
- **Evaluation harness containment:** schema v2 accepts only path-safe case IDs, uses one collision-free trial key for every artifact, and proves every recorded path stays within its run directory.
- **Evaluation completeness:** validation reconstructs the exact case × repetition set from the hashed eval source, checks canonical prompt contents and artifact paths, and rejects omitted, duplicated, prepared, or empty-response trials in a completed run.
- **Evaluation failure states:** timeouts safely decode partial byte output; missing runners, nonzero exits, empty output, and interruptions end in explicit terminal states rather than leaving a misleading `running` manifest. Grading now requires a recorded prompt version.
- **Private runner metadata:** exact runner arguments are opt-in with `--record-runner-argv`; the default records an executable name and argv hash without persisting possible credentials.
- **Framework guidance:** corrected the Textual/HTTPX async worker, documented Ratatui's non-transactional `try_init`/`try_restore` behavior, fixed Ink 7 Backspace naming and `<Static>` scope, removed picocolors from the ESM-only list, and corrected Cobra application-completion commands.
- **Picker behavior:** reconciled fzf's full-screen default with explicit bounded `--height` mode and reserved printable `hjkl` for views or modes where text entry does not own those keys.
- **CLI contracts:** replaced universal `--no-input` language with an ecosystem-appropriate noninteractive contract, distinguished `/dev/tty` pickers from stdio prompts, corrected exit-code-2 attribution, and marked BSD `sysexits` legacy/nonportable.
- **Responsive wording:** geometry may derive from the latest stored window dimensions when a framework's render method has no frame; cached rectangles must be invalidated on resize.

### Changed
- **Trigger boundary:** the skill description now explicitly excludes browser/web UI, native GUI, editor/font configuration, and backend or shell work with no terminal interface. This addresses the committed v1.5 trigger set's known near-miss activations while preserving terminal-specific triggers.
- **Exact package contract:** source and archive validation now enforce the declared ten-file allowlist and reject symlinks, caches, generated files, unexpected directories, wrong modes, wrong timestamps, or wrong archive order.
- **CI hardening:** workflows pin actions by commit, run ShellCheck, and run Claude's strict plugin validator with a pinned CLI on Node 22.20. The documented release flow builds and verifies a draft's asset before publication.
- **Installer documentation:** `npx skills` examples pin a tested CLI version, state its Node requirement, name the target agent explicitly, and clarify project-local versus agent-global installation.
- **Evidence wording:** the v1.6.0 structural report remains preserved, but its 14/14 is identified as a targeted composite recheck rather than a full rerun of every case against the final tree.

### Added
- **Regression coverage:** expanded the harness/package suite from two tests to thirteen, covering traversal, sanitized-name collisions by rejection, exact trial coverage, state consistency, empty output, partial timeout output, missing runners, private argv, grader metadata, exact archives, symlinks, and unexpected package files.
- **Correction evals:** added `evals/v161-correction-evals.json` for Python async HTTP, Ratatui fallible lifecycle handling, fzf key/screen contracts, Ink virtualization and Backspace, Cobra completion, noninteractive CLI behavior, and portable exit-code guidance.
- **Single-snapshot forward evidence:** ran all seven correction cases against clean commit `7d68d6080ba7772febfad315e042d717b4804c37` with OpenAI Codex desktop CLI `0.147.0-alpha.6.5`, exact model `gpt-5.6-terra`, high reasoning, and one repetition. The separately graded schema-v2 run scored 25/25; raw prompts, answers, stderr traces, hashes, grades, and summary are preserved under `evals/results/v1.6.1-forward-test/`.

## [1.6.0] — 2026-08-18

Structural release focused on efficient context use, single-source guidance, Codex presentation metadata, and reproducible evaluation evidence. The trigger description remains unchanged because the v1.5 trigger set showed no positive misses; this release changes what loads after activation, not when activation occurs.

### Changed
- **Slim procedural core:** `SKILL.md` is now a 139-line routing, workflow, and cross-cutting-contract layer (down from 314 lines). Detailed layouts, visual rules, interactions, framework APIs, and case studies stay in their authoritative references and load only when the task needs them.
- **Single-source ownership:** the core now names which reference owns each topic, and the four ecosystem-local “Idioms summary” sections were removed because they repeated guidance already present in the same files. Release validation rejects exact long-paragraph duplication across the core and references and enforces a 200-line core budget.
- **Bubble Tea safety placement:** the `RestoreTerminal` correction now lives beside the Go lifecycle example, preventing the framework-specific warning from becoming a misleading universal rule.

### Added
- **Codex metadata:** generated `agents/openai.yaml` with a concise UI description and a default prompt that explicitly invokes `$tui-design`; the validator checks its shape and the packaged archive now requires it.
- **Reproducible eval harness:** `scripts/eval_harness.py` prepares baseline or clean-context with-skill prompts, runs any stdin/stdout model command without a shell, and records exact provider/model labels, repetitions, git state, host data, input hashes, raw outputs, timing, and exit status. Separate scoring and validation phases enforce full rubric coverage and detect artifact tampering.
- **Harness tests:** standard-library integration tests cover prompt injection, repeated trials, scoring, manifest integrity, and tamper detection. They run inside `validate-release.sh` and CI.
- **Structural forward tests:** added `evals/v160-structural-evals.json` and preserved the raw clean-context answers in `evals/results/v1.6.0-forward-test/`. The first pass scored 12/14; after tightening named-framework routing, case 2 was rerun at 5/5. The report's 14/14 combines unchanged cases 0–1 from the initial pass with that targeted recheck, rather than a full final-tree rerun. It also records that the in-app runner did not expose its exact inherited model identifier, so this evidence is not a reproducible comparative benchmark.

## [1.5.1] — 2026-08-18

Correctness and release-engineering patch for the 1.5 line. This release removes unsafe or over-broad guidance found in a full review of 1.5.0, updates the assertions that guard those behaviors, and makes the published `.skill` artifact reproducible and tag-accurate.

### Fixed
- **Terminal cleanup:** removed the harmful Bubble Tea `defer p.RestoreTerminal()` pattern and now prefers each framework's managed lifecycle. Ratatui guidance correctly installs `color_eyre` before `run()`/`init()` so Ratatui's restoration hook wraps the reporting hook; custom hooks are limited to manual `Terminal` setup.
- **Color guidance:** current Lipgloss examples use v2 `LightDark` (with `AdaptiveColor` identified only as v1/compat), truecolor is detected rather than assumed, and blanket claims that `owo-colors` or JavaScript color libraries automatically honor `NO_COLOR` are replaced with an explicit output policy and force/disable precedence.
- **Screen-mode and responsive guidance:** fzf is accurately described as full-screen by default with explicit bounded `--height` mode. Inline rendering is a strong default for bounded pickers, not a universal rule. `80×24` is a test baseline rather than a universal minimum, with application-specific truthful minimums.
- **Interaction guidance:** command palettes, persistent footers, `hjkl`, live validation, and theme/community-palette support are scoped to apps that benefit from them. Settings may validly use Apply/Save/Cancel when changes are atomic, expensive, or remote.
- **Portability and accessibility:** resize handling is expressed through framework events rather than universal `SIGWINCH`; suspend behavior is capability-aware; redraw guidance permits intentional tick-driven updates; accessibility language no longer treats every TUI as categorically inaccessible.
- **Eval assertions:** cleanup assertions now accept framework-managed behavior and explicitly reject the Bubble Tea restoration misuse; the fzf assertion now names `--height` rather than claiming fzf renders inline by default. Added `evals/v151-correction-evals.json` for the corrected edge cases.

### Changed
- `.skill` packaging now normalizes archive order, timestamps, and permissions for byte-for-byte repeatability.
- Added `scripts/validate-release.sh` and pull-request/main validation CI for manifest parity, changelog/version agreement, skill structure, reference links, Markdown fences, eval JSON, archive integrity, and deterministic packaging.
- Release-asset CI now checks out and validates the exact release tag, including manual backfills, before building or uploading the asset.
- Removed ignored top-level marketplace metadata fields so the marketplace passes strict schema validation without warnings.

## [1.5.0] — 2026-07-10

Tier-3 round: a fresh structural/coverage audit of the shipped v1.4.0 skill (post-expansion consistency, the remaining content-gap backlog, and a 12-question user-lens routing review), followed by fixes and four new content areas — shell integration, forms/settings-screen design + CLI first-run auth flows, Nerd Font glyph conventions + degraded-state UX, and per-ecosystem performance profiling. Content written from six web-verified research briefs (`tui-design-workspace/tier3/research/`, gitignored). Validated with a four-eval with/without comparison (`evals/tier3-content-evals.json`): baseline **55%** vs with-skill **95%** — a real, consequential lift this round (unlike v1.4.0's statistical wash), because this content targets areas where plausible-sounding reasoning was verifiably *wrong*, not just under-specific. Two standout catches: the baseline confidently recommended Textual's `DataTable.add_rows()` as a bulk-insert optimization (it's just a loop over `add_row()`, per Textual's own source) and told a user building "a specialized yazi" to skip yazi's own real `--cwd-file` mechanism, calling it "strictly worse."

The research phase hit a platform-wide rate limit when the first wave of research agents fanned out into their own sub-agents (~15-20 concurrent calls); all four briefs were lost before writing output. Recovered two completed sub-agent results from before the failure, then retried the rest at controlled concurrency with explicit no-fan-out instructions.

### Fixed
- **Routing break:** `ecosystem-python.md` now has a `## Debugging` section (previously folded into "Dev tools"), matching the routing table's promise that all four ecosystem files have Testing/Debugging sections.
- **`visual-patterns.md`:** the Overlay/popup layout entry no longer contradicts the "Inline, alt-screen, or overlay" section added in v1.4.0 — it now points to that section instead of flatly saying "use the alternate screen."
- **The three-way fzf/lazygit/k9s/helix pattern duplication** (flagged in the v1.4.0 audit, unfixed until now): `interaction-patterns.md` now owns the recipe, `exemplar-apps.md` owns only app-specific facts, each cross-links the other. Net −40 lines in `exemplar-apps.md`.
- **SKILL.md:** un-lagged the review checklist — "should this even be full-screen?" is now the first question (not "does it use the alt screen"), plus a new OSC-52/8/9 checklist item; the "Patterns worth naming" section trimmed to a pure index with dual pointers; a duplicated logging-rule sentence removed. Net: flat at 314 lines.
- Added a `vhs-cli-demos` routing row — the skill previously never mentioned the author's own sibling skill for demo-GIF capture, discoverable only via two incidental VHS mentions in `ecosystem-go.md`.
- ToCs added to all four ecosystem reference files (400–500+ lines each, previously none).

### Added
- **`cli-basics.md` — "Shell integration"**: the parent-cwd/env impossibility, yazi's and ranger's real `--cwd-file`/`--choosedir` wrapper-function pattern (exact verified shell code), the `eval "$(tool init shell)"` pattern (starship/zoxide/atuin/mise/fzf compared), and the never-silently-edit-rc-files etiquette.
- **`cli-basics.md` — "Shipping, updates, and telemetry"**: distribution-shape trade-offs (compiled binary + Homebrew tap vs npm `optionalDependencies` vs pure npm/pipx — including that GoReleaser's Homebrew Formulas publisher is deprecated as of v2.10), update-check etiquette (gh/npm's `update-notifier` conventions, defer-to-the-package-manager), and telemetry etiquette (verified: `DO_NOT_TRACK` is real but far from universal — Next.js/Vercel/Prisma/Netlify all decline it despite open requests; `consoledonottrack.com` itself has lapsed and is now squatted).
- **`cli-basics.md` — "First-run authentication"**: the two dominant patterns (OAuth device-code + keychain vs prompt + plaintext file), TTY-detection done right (both stdin *and* stdout), the env-var-short-circuits convention, and per-ecosystem keychain libraries (including that `keytar` has been dead since December 2022).
- **`interaction-patterns.md` — "Forms and settings screens"**: validation timing (never per-keystroke — huh/Clack/Inquirer all agree; Textual defaults to all three triggers and should be narrowed), the corrected finding that no framework has a built-in "required field" marker (huh's `" *"` is the *error* indicator, not required), huh's real conditional-visibility API (`WithHideFunc` is group-level, not per-field), and an honest settings-screen framing (live-apply like htop, or defer to `$EDITOR` like lazygit — there's no attested Save/Cancel-with-dirty-tracking convention).
- **`visual-patterns.md` — "Icons and Nerd Fonts"**: verified that no terminal exposes a font-detection signal; real opt-in conventions (eza, lazygit, yazi) and the Nerd Fonts v2→v3 codepoint break that necessitates lazygit's version selector.
- **`visual-patterns.md`** extended "Empty states and loading states" with disconnected/stale-data UX (k9s's real retry config; btop's open bug as a documented anti-pattern to avoid) and honestly-hedged timeout/cancel UX guidance.
- **Per-ecosystem profiling**, added to each `Debugging` section: Go (`net/http/pprof` on a loopback port — verified from Charm's own `crush`, not file-based `pprof`), Rust (`cargo flamegraph` plus the verified raw-mode-intercepts-Ctrl+C gotcha; confirmed ratatui.rs has no official profiling recipe), Python (`py-spy` plus its asyncio `--idle` gotcha), TypeScript (`node --cpu-prof`, plus the verified finding that React DevTools' Profiler tab does not work with Ink's custom renderer — only the Components tab does).
- `evals/tier3-content-evals.json` — the four-eval set as a reproducible artifact.

## [1.4.0] — 2026-07-03

Tier-2 content expansion closing the four zero-coverage areas identified by the v1.3.0 audit: testing, debugging, inline-vs-alt-screen, and OSC escapes. All content written from web-verified research briefs (per-claim sources; unverifiable claims omitted or hedged), then validated with a six-eval with/without comparison (`evals/tier2-content-evals.json`). Honest result on a frontier model: strategy-level pass rates are already saturated (29/30 both sides); the measured lift is *specifics* — the with-skill run fixed both baseline factual errors (tmux `set-clipboard external` semantics; the OSC 52 clipboard-read security issue) and averaged −20s / −1.4k tokens per answer. The content's larger value is insurance for smaller models and against ecosystem drift.

### Added
- **SKILL.md — "Testing and debugging"** (three-layer pyramid: pure update-layer unit tests → pinned-size/profile golden/snapshot → sparing PTY e2e; the never-print-to-the-owned-terminal rule), inline-vs-alt-screen as a first-class decision in the routing table, decision flow, and layouts list, and an OSC pointer. 299 → 314 lines; description untouched.
- **`ecosystem-go.md` — Testing + Debugging**: teatest/v2 (correct import — it stayed on `github.com/charmbracelet/x`, not charm.land), v2 `KeyPressMsg` unit-test literals, executing returned Cmds, golden files + `-update`, CI determinism via `WithProgramOptions(tea.WithColorProfile(colorprofile.Ascii))`, the crush-skips-teatest signal; `tea.LogToFile` + `DEBUG` + headless delve.
- **`ecosystem-rust.md`**: insta color/style caveat, multi-size testing with odd sizes + pure `compute_layout`, gitui/openai-codex real-world anchors; Debugging section (tracing-to-file, in-app debug pane, tui-logger, second-terminal debugger attach).
- **`ecosystem-typescript.md`**: ink-testing-library staleness correction (v4 pins Ink 5; `stdin.write` unreliable on Ink 6/7) with the Gemini CLI vitest-harness + node-pty pattern; Debugging section (`patchConsole` semantics, `debug: true` frame-append, React DevTools, stderr discipline).
- **`ecosystem-python.md`**: `run_test()` gotchas (headless 80×24, notifications/tooltips off by default), message assertion via recorder handler or `message_hook`, validation-testing wiring, `textual-dev` package note.
- **`visual-patterns.md` — "Inline, alt-screen, or overlay — where the UI lives"**: live-in vs summon rule, verified per-framework mechanics (Bubble Tea v2 view field, Ink 7 `alternateScreen`, Textual `run(inline=True)`, Ratatui `Viewport::Inline` + `insert_before`), the fzf `--height`//dev/tty model, and the receipt-pattern exit contract (gum's stderr-UI/stdout-result mechanics).
- **`interaction-patterns.md` — "Talking to the terminal emulator — OSC 8, 52, 9"**: support matrices, the Ratatui OSC 8 gap, `file://`-opens-locally caveat, OSC 52 size ceilings and tmux `set-clipboard on|external` semantics (no passthrough needed), write-only clipboard security posture, OSC 9/777 notification etiquette.
- **`evals/tier2-content-evals.json`** — the six-eval set (reproducible artifact), assertions graded against the research ground truth.

### Fixed
- SKILL.md's overlay-layout bullet no longer says "use the alternate screen" unconditionally — fzf-class tools may be inline with bounded height; pointer to the new section.
- Theming section: lingering v1 `AdaptiveColor` reference updated to `LightDark` (missed in 1.3.0).

## [1.3.0] — 2026-07-03

Accuracy and freshness pass driven by a full parallel audit of all nine files, with every load-bearing claim re-verified against upstream docs (pkg.go.dev, crates.io, PyPI, npm, project changelogs). The May eval rounds validated the skill's *behavior*; this audit targeted the other axis — whether the code snippets and version claims are still true — and found the rot concentrated in the fastest-moving ecosystems.

### Fixed
- **Go (`ecosystem-go.md`) — the Bubble Tea section no longer contradicts itself.** It declared v2 stable while every snippet used v1 APIs that don't compile on v2. The canonical example, options list, and mental model now use the real v2 API (`tea.KeyPressMsg`, `View() tea.View`, alt-screen/mouse declared on the view — `tea.WithAltScreen()`/`WithMouse*` were removed). Lipgloss v2 guidance rewritten (`LightDark` + `HasDarkBackground`; `AdaptiveColor` relegated to `compat`; `SetColorProfile` replaced by write-time downsampling + `tea.WithColorProfile`). Huh v2 full-screen via `WithViewHook`. v2 stable date corrected to February 2026.
- **TypeScript (`ecosystem-typescript.md`) — brought from Ink 5-era to Ink 7.** ESM boundary corrected (v4, not v5 — the file contradicted itself), `useApp()` API fixed (no `exitWithError`), native `alternateScreen` render option, new hooks (`usePaste`, `useCursor`, `useAnimation`, `useBoxMetrics`), aria-* accessibility props, Node 22 / React 19 floor, backspace/`key.delete` migration trap. OpenTUI attribution corrected (Anomaly, not sst) and `@opentui/three` added.
- **Python (`ecosystem-python.md`):** two broken snippets fixed (`push_screen_wait` requires `@work`; `Static.renderable` → `.content` since Textual 6.0). Added the Textualize wind-down status note (company gone mid-2025; Textual alive at 8.x, maintained by Will McGugan) with the 6.0/8.0 breaking renames. urwid un-"legacy"-ed (v4.0 revival); textual-web hedged in favor of `textual serve`.
- **Rust (`ecosystem-rust.md`):** Ratatui 0.30 now described as stable (Dec 2025; 0.30.2 current); invented `StatefulWidgetState` type corrected to the associated `State` types; Dioxus TUI demoted to abandoned; crossterm 0.29 named as the current pin.
- **Cross-cutting:** removed the leftover duplicate "Responsive design" section in `visual-patterns.md` whose three-band ladder conflicted with the canonical four-band one; fixed the nonexistent Bubbles `MultiProgress`; Textual command palette corrected to `Ctrl+P` (moved off `Ctrl+\` in v0.77 — which also resolved a self-contradiction with the reserved-keys rule); `Ctrl+I`-for-invert replaced (it's Tab in legacy encoding); helix corrections (file explorer merged Jan 2025; `C` not `,C` for multi-cursor; own pickers, not telescope); yazi bookmark bullet dropped (was ranger's bindings); gotop de-peered (archived 2020).

### Added
- New-in-ecosystem entries: **Fang**, **Crush**, **Ultraviolet** (Go); **Ratzilla**, **tui-realm**, **mousefood** (Rust); **Toad** (Python); Clack 1.x / bombshell-dev status (TS).
- Table of contents at the top of the four cross-cutting reference files; `exemplar-apps.md`'s "How to use this file" index moved from bottom to top.
- `cli-basics.md`: the `-f` (`--file` vs `--force`) collision caveat; concrete macOS config-path recommendation.

### Changed
- `evals/build-evals.json`: the Go assertions no longer hardcode v1-only API (`tea.WithAltScreen`) — they now accept the v1 or v2 idiom, matching the corrected reference content.

## [1.2.0] — 2026-05-31

Adds two proactive review reflexes, validated with an eval-driven loop (design-review prompts, with-skill vs. baseline, scored across repeated runs to separate signal from model variance). The motivation: a strong base model already critiques layouts well *when prompted directly* — the skill's leverage is making it do so **consistently and unprompted**.

### Added
- **The clutter audit (`SKILL.md` + `visual-patterns.md`):** a countable method for density judgment — border-nesting depth, signals-per-state, always-on markers, chrome-vs-data ratio, and the removal test — so "feels busy" becomes named, specific cuts instead of "simplify it." Measurably increased the quantified specificity of clutter critique across runs.
- **Responsive design — breakpoints and the floor (`visual-patterns.md`):** a dedicated section with the breakpoint ladder (wide >120 / standard 80–120 / narrow 60–80 / too-small) and the mechanics (relative units, load-bearing-element priority, `SIGWINCH`, an 80×24 minimum with a too-small message). `SKILL.md` now instructs both reflexes be applied to any layout review **even when the user only asked about something else** — the most-missed behavior in practice.

### Changed
- `SKILL.md` review checklist and the new-project decision flow now reference the clutter audit and the breakpoint ladder directly, so the reflexes fire from every entry point.

## [1.1.0] — 2026-05-31

Freshness and accuracy pass on the ecosystem references. No structural changes; all routing and universal principles are unchanged.

### Changed
- **Go (`ecosystem-go.md`):** Bubble Tea v2 is documented as stable rather than "in beta." Added the v2 highlights (Cursed Renderer, pure Lipgloss, progressive keyboard enhancements), the new `charm.land/bubbletea/v2` import path, and a short v1 → v2 migration note.
- **Rust (`ecosystem-rust.md`):** Named the current 0.30 line (modular workspace crates, `no_std`) and replaced the vague "0.30+ feature flags" with the actual `crossterm_0_28` / `crossterm_0_29` compatibility flags and guidance on picking one.
- **Star counts:** Removed hardcoded GitHub star/download numbers (Ratatui, Textual, Bubble Tea, tview) that go stale, in favor of durable relative phrasing ("the most widely used," "dominates").
- **README:** Updated a contributing example that referenced Bubble Tea v2 as an upcoming event.

## [1.0.0]

Initial release. Universal TUI/CLI design principles in `SKILL.md` routing to eight reference files covering the Go, Rust, Python, and TypeScript ecosystems plus CLI basics, visual patterns, interaction patterns, and exemplar apps.

[Unreleased]: https://github.com/gfargo/tui-design-skill/compare/v1.8.2...HEAD
[1.8.2]: https://github.com/gfargo/tui-design-skill/compare/v1.8.1...v1.8.2
[1.8.1]: https://github.com/gfargo/tui-design-skill/compare/v1.8.0...v1.8.1
[1.8.0]: https://github.com/gfargo/tui-design-skill/compare/v1.7.4...v1.8.0
[1.7.4]: https://github.com/gfargo/tui-design-skill/compare/v1.7.3...v1.7.4
[1.7.3]: https://github.com/gfargo/tui-design-skill/compare/v1.7.2...v1.7.3
[1.7.2]: https://github.com/gfargo/tui-design-skill/compare/v1.7.1...v1.7.2
[1.7.1]: https://github.com/gfargo/tui-design-skill/compare/v1.7.0...v1.7.1
[1.7.0]: https://github.com/gfargo/tui-design-skill/compare/v1.6.1...v1.7.0
[1.6.1]: https://github.com/gfargo/tui-design-skill/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/gfargo/tui-design-skill/compare/v1.5.1...v1.6.0
[1.5.1]: https://github.com/gfargo/tui-design-skill/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/gfargo/tui-design-skill/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/gfargo/tui-design-skill/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/gfargo/tui-design-skill/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/gfargo/tui-design-skill/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/gfargo/tui-design-skill/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/gfargo/tui-design-skill/releases/tag/v1.0.0
