# Changelog

All notable changes to the `tui-design` skill are documented here. The format is loosely based on [Keep a Changelog](https://keepachangelog.com/), and the project follows semantic versioning.

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
