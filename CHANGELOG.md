# Changelog

All notable changes to the `tui-design` skill are documented here. The format is loosely based on [Keep a Changelog](https://keepachangelog.com/), and the project follows semantic versioning.

## [Unreleased]

### Added
- **Schema-v4 grading-prompt integrity:** grades now record `grading_prompt: {path, sha256}`, machine-linking `grader.prompt_sha256` to a grading-prompt file preserved inside the same evidence bundle. The harness enforces bundle containment and rejects path traversal, missing files, and digest mismatches. Schema v2 and v3 evidence remains readable and valid under their original, unchanged rules.

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
