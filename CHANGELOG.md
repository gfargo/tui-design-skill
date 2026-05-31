# Changelog

All notable changes to the `tui-design` skill are documented here. The format is loosely based on [Keep a Changelog](https://keepachangelog.com/), and the project follows semantic versioning.

## [1.1.0] — 2026-05-31

Freshness and accuracy pass on the ecosystem references. No structural changes; all routing and universal principles are unchanged.

### Changed
- **Go (`ecosystem-go.md`):** Bubble Tea v2 is documented as stable rather than "in beta." Added the v2 highlights (Cursed Renderer, pure Lipgloss, progressive keyboard enhancements), the new `charm.land/bubbletea/v2` import path, and a short v1 → v2 migration note.
- **Rust (`ecosystem-rust.md`):** Named the current 0.30 line (modular workspace crates, `no_std`) and replaced the vague "0.30+ feature flags" with the actual `crossterm_0_28` / `crossterm_0_29` compatibility flags and guidance on picking one.
- **Star counts:** Removed hardcoded GitHub star/download numbers (Ratatui, Textual, Bubble Tea, tview) that go stale, in favor of durable relative phrasing ("the most widely used," "dominates").
- **README:** Updated a contributing example that referenced Bubble Tea v2 as an upcoming event.

## [1.0.0]

Initial release. Universal TUI/CLI design principles in `SKILL.md` routing to eight reference files covering the Go, Rust, Python, and TypeScript ecosystems plus CLI basics, visual patterns, interaction patterns, and exemplar apps.
