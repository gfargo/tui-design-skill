---
name: tui-design
description: Design and build clean, professional, minimal terminal UI (TUI) applications and command-line tools. Use this skill whenever the user is building, designing, refactoring, reviewing, or asking about terminal interfaces — full-screen TUIs (file managers, dashboards, monitors, git/k8s tools, REPLs), interactive CLI prompts, or simple command-line utilities. Use it for library questions ("Bubble Tea vs Ratatui vs Textual vs Ink"), design questions ("how should I lay out this dashboard"), and concrete build requests ("build me a TUI for X"), even when the user doesn't say "TUI" explicitly — phrases like "terminal app", "ncurses-style", "interactive shell tool", "CLI dashboard", "fzf-like picker", or naming a known TUI app (lazygit, k9s, btop, helix, yazi) all qualify.
---

# TUI & CLI Design

Build terminal applications that feel professional — the way `lazygit`, `k9s`, `btop`, `helix`, `fzf`, and `yazi` feel. The terminal is enjoying a renaissance: Charm (Go), Ratatui (Rust), Textual (Python), and Ink (TypeScript) have each crystallized a mature philosophy. This skill teaches the universal patterns that make TUIs feel good plus per-ecosystem deep-dives in `references/`.

## When to read which reference

Use this skill's body for the **universal principles** below. Then load reference files on demand:

| Situation | Read |
|---|---|
| User picked Go / mentioned Bubble Tea, Charm, Lipgloss, tview, gocui | `references/ecosystem-go.md` |
| User picked Rust / mentioned Ratatui, crossterm, tui-rs, Cursive | `references/ecosystem-rust.md` |
| User picked Python / mentioned Textual, Rich, prompt_toolkit, urwid | `references/ecosystem-python.md` |
| User picked TS/JS / mentioned Ink, blessed, OpenTUI, Clack, Inquirer | `references/ecosystem-typescript.md` |
| Building a non-interactive CLI (no full-screen UI) | `references/cli-basics.md` |
| Designing layout, borders, color, typography, density | `references/visual-patterns.md` |
| Designing keybindings, focus, navigation, modal vs modeless | `references/interaction-patterns.md` |
| Studying what makes specific apps great (lazygit, k9s, fzf, btop, helix, yazi, atuin) | `references/exemplar-apps.md` |
| Testing or debugging a TUI | that ecosystem's `references/ecosystem-*.md` (Testing / Debugging sections) |
| Inline vs full-screen; clipboard, hyperlinks, notifications (OSC) | `references/visual-patterns.md` → *Inline, alt-screen, or overlay*; `references/interaction-patterns.md` → *Talking to the terminal emulator* |

If the user hasn't named a language, ask which ecosystem before diving into framework specifics. The universal principles below apply regardless.

---

## The terminal is a constrained design medium

Every cell is the same width. Type size doesn't change. You have ~80×24 characters at the small end, maybe 200×60 if you're lucky. You can't draw arbitrary pixels; you compose grids of characters with foreground/background colors and a handful of attributes (bold, dim, italic, underline, reverse). These constraints are the **point** — they force clarity. When something feels cramped or noisy in a TUI, the answer is almost never "add more"; it's usually "remove something or use whitespace."

Three observations that drive everything else:

1. **Spatial memory is the navigation.** Users learn where things live: the file list is left, the diff is right, the status bar is bottom. Once that's established, panels must never move without explicit action. Reordering panels on focus is among the worst sins a TUI can commit.
2. **Color encodes meaning, not appearance.** Treat colors as semantic tokens (`status.error`, `text.muted`, `accent.primary`), not raw hex codes. The app should be *usable in monochrome* — color is enhancement, never the only signal. ~8% of males have red-green CVD; pair color with letters or symbols.
3. **Keyboard is primary; mouse is augmentation.** Every action must be reachable from the keyboard. Mouse can speed things up but never gates functionality. Vim motions (`hjkl`, `/`, `?`, `Esc`, `q`, `gg`, `G`) are the lingua franca even for non-vim users — supporting them is a courtesy that costs nothing.

## The seven canonical layouts

Most successful TUIs use one of these. Choose by workflow shape, not by aesthetics:

- **Persistent multi-panel** — All panels visible in fixed positions, focus shifts between them. Numeric keys (`1`–`5`) jump directly. Used by **lazygit, btop, htop**. Best for at-a-glance observation and switching between views of related state.
- **Miller columns** — Three (or N) columns: parent → current → preview. `h`/`l` ascend/descend. Used by **yazi, ranger, broot**. Best for hierarchies (filesystems, JSON, K8s resources). Degrades poorly on narrow terminals — provide a single-pane fallback.
- **Drill-down stack** — Browser-style: navigate deeper with a back-stack, `Esc` returns. Often paired with command-mode navigation (`:pods`, `:nodes`). Used by **k9s, lazydocker**. Best when there are many resource types and the user needs to pivot between them.
- **Widget dashboard** — Independent widgets in a grid, each owning its data lifecycle. Layout configurable via TOML/YAML. Used by **bottom, btop, glances**. Best for monitoring/observability where users want to compose their own view.
- **IDE three-panel** — Sidebar → main content → detail/output, often with tabs in the main panel. Used by **Posting, Harlequin, helix**. Best for editor-like workflows.
- **Overlay / popup** — Appears over the shell, does one thing, exits. Used by **fzf, atuin, zoxide+fzf**. Best for "summon → choose → output" interactions. Render either full-screen on the alternate screen or inline with a bounded height (fzf's `--height`); either way, clean up on exit and print the result to stdout. See `references/visual-patterns.md` → *Inline, alt-screen, or overlay*.
- **Tabbed within panel** — Tab bars cycled with `[`/`]`. Used inside larger layouts (lazygit's Local/Remotes/Tags, lazydocker's Logs/Stats/Env tabs). Best when one panel needs multiple personalities without changing the global layout.

The universal rule: **panels never move without explicit user action.**

## Visual hierarchy without varying type size

Since you can't change font size, hierarchy comes from:

- **Position** — top/left reads first; status bar at bottom; headers at top.
- **Color and weight** — bold + accent color for titles and focused panel borders; dim for metadata, timestamps, disabled items; default weight for primary text.
- **Reverse video** — universally available since VT100; the canonical way to mark current selection. Works on every terminal.
- **Indentation and connectors** — `├─ └─` for trees; consistent indent units (2 cells is standard).
- **Whitespace and bullets** — `▶` expandable, `▼` expanded, `●` active, `○` inactive, `•` static bullet.
- **Borders for focus** — border *color* change is the strongest focus indicator. Lipgloss, Ratatui, Textual, and Ink all support per-side border styling.

Use **bold** for titles, selection labels, and primary content. Use **dim** for metadata and disabled items. Use **italic** sparingly (poorly supported on many terminals — never the only signal). Use **underline** for hyperlinks (OSC 8) and shortcut hints. Use **reverse video** for the cursor row and current selection. Avoid blink (disabled in most modern terminals; accessibility hazard) and strikethrough (limited support).

## Color as a semantic system

Design in three tiers:

1. **Monochrome** — does the app work with `NO_COLOR=1`? If layout, weight, and reverse video carry the meaning, yes.
2. **16 ANSI** — does it look right with the user's theme (Solarized, Gruvbox, whatever)? You don't control these; theme-coherent palettes do.
3. **256 / truecolor** — fine-grained palette for designed themes (Catppuccin, Dracula, Nord). Detect via `$COLORTERM=truecolor`.

**Always respect `NO_COLOR`** (no-color.org). `ripgrep`, `bat`, `eza`, `delta`, `fd` all do.

Conventional meanings have crystallized:
- **Green** → success, added, online
- **Red** → error, deleted, danger
- **Yellow** → warning, modified, pending
- **Cyan / Blue** → info, paths, links
- **Magenta** → special, highlights
- **Dim / gray** → secondary, disabled

Define semantic tokens (`status.error`, `git.staged`, `text.muted`) and theme them. Lipgloss's `LightDark` (v2; `AdaptiveColor` in v1/compat), Textual's CSS variables, and Ratatui's palette pipelines all implement this indirection. Scattering hex codes through code is a phase you grow out of.

**Never use color alone.** Pair with letters (lazygit's file status: `M` modified, `A` added, `D` deleted, `??` untracked) or symbols (delta's `+`/`-` line prefixes). Safe color pairs for CVD: blue+orange, blue+yellow, black+white.

## Borders, density, and whitespace

Use single-line borders (`─ │ ┌ ┐ └ ┘`) by default. Rounded (`╭ ╮ ╰ ╯`) is the modern Charm aesthetic — fine, slightly softer. Heavy (`━ ┃ ┏`) for emphasis sparingly. **Avoid double-line** (`═ ║ ╔`) — it reads as "DOS." Always provide ASCII fallback (`+`, `-`, `|`) for legacy SSH and `TERM=dumb`.

When to use borders vs whitespace:
- **Borders** — when the pane has dynamic content needing a visible boundary, when focus state must be shown, when adjacent panels need clear separation.
- **Whitespace alone** — when content is static (htop has no internal borders) or density matters more than structure. A single blank row often beats a heavy border.

Density choices:
- **Pack** when data is scanned at a glance, updates in real time, or is read horizontally across rows (htop, btop, k9s).
- **Pad** when reading prose, filling forms, or making single decisions (gum/huh forms, Glow markdown, Posting).

Don't decorate. Borders that exist purely for "looks polished" usually make the app feel busier without adding meaning.

## Two reflexes to apply unprompted

These are the two things the default instinct misses most, because users rarely ask for them by name — and a strong base model will answer the literal question without raising either. Apply both to **any** layout you design or review, even when the user asked about something else entirely (a color choice, a keybinding, "why does this feel busy"). This is where most of the value is.

**1. Run a clutter audit — make "feels busy" countable.** Never answer "it feels noisy" with "simplify it." Count the offenders and name the specific cuts: border-nesting depth (more than *one* border between the terminal edge and the content is too many; an outer full-screen frame is almost always redundant), how many separate signals encode the same state (`[PASS]` + green + `✅` + a row marker is four), markers that sit on every row (a glyph on 100% of rows marks nothing), and the ratio of cells spent on chrome — borders, labels, repeated boilerplate like a full datestamp on every log line — versus actual data. The full method is in `references/visual-patterns.md` → *The clutter audit*.

**2. Pressure-test the floor.** A layout designed at the author's own window size is unfinished — they never see it break because they only ever see their own terminal. State concretely what happens at **80×24 and a 60-column tmux split**: what collapses to a single pane, what hides, what truncates, and the "terminal too small" message below the minimum. Multi-column layouts (Miller columns, 2×N grids) must have a single-pane fallback. **Raise this in every layout review even when size was never mentioned** — it is the single most-missed issue in TUI design, and "it looks great on my screen" is exactly the blind spot it addresses. Breakpoint ladder in `references/visual-patterns.md` → *Responsive design*.

## Tables and lists

Always:
- **Align numerics right, text left, dates as fixed-width ISO-8601.**
- **Truncate, don't wrap, in cells.** Tail truncation (`/usr/local/share/...`) for paths in lists. Middle truncation (`/usr/.../file.txt`) when the basename matters. Reserve a cell for the ellipsis.
- **Show a count** (`123/45678` like fzf does) when filtering.
- **Sort indicator** (`▲`/`▼`) on the active column.
- **Detail-on-Enter** as the universal escape hatch — pressing Enter on a row reveals all fields in a side panel or modal. This lets you hide low-priority columns at narrow widths without losing access to the data.
- **Virtualize** any list that might exceed a few hundred items. k9s renders thousands of pods, Toolong tails multi-GB logs — both virtualize. Built into Textual `DataTable`, Ratatui `Table`+`TableState`, Bubbles `list`, Ink with `<Static>`.

## Status bars, headers, footers

The convention that has converged across nearly every modern TUI:

- **Header (top)** — persistent context: what app, what dataset, what mode. htop's CPU/mem meters; k9s's cluster/context/namespace; lazygit's branch and repo.
- **Main area (middle)** — the panels. This is where the work happens.
- **Status / mode line** — ephemeral feedback ("Saved", "3 files changed") with auto-fade. Vim-style mode indicators (NORMAL/INSERT/SELECT) with distinct cursor shapes.
- **Footer hint bar (bottom)** — 3–5 most-useful shortcuts always visible, full reference behind `?`.

The footer hint bar is the single most important discoverability tool. htop's F1–F10 strip; lazygit's per-pane hints; Bubble Tea's `bubbles/help` auto-generates from the keymap; Textual's `Footer` widget renders bindings declared via `BINDINGS`. **Don't make users read docs to discover basic actions.**

## Keys: discoverability and conventions

**Cross-app conventions** that have crystallized — use these unless you have a strong reason not to:

| Key | Action |
|---|---|
| `q` | quit |
| `?` | help |
| `/` | search |
| `n` / `N` | next / prev match |
| `Esc` | cancel / back |
| `Enter` | confirm / drill in |
| `Space` | toggle / mark for multi-select |
| `:` | command mode |
| `gg` / `G` | top / bottom |
| `Tab` / `Shift+Tab` | switch focus |
| `r` | refresh |
| `1`–`9` | jump to panel / numbered tab |
| `hjkl` *and* arrows | move (support both) |

**Never bind these — they belong to the terminal:**
- `Ctrl+C` (SIGINT — should always quit cleanly)
- `Ctrl+Z` (SIGTSTP — suspend; you must restore terminal state on resume)
- `Ctrl+\` (SIGQUIT)
- `Ctrl+S` / `Ctrl+Q` (XON/XOFF flow control on legacy terminals)

**Discoverability is layered:**

1. Always-visible footer hints (3–5 most useful keys)
2. `?` opens a help screen with all bindings
3. Leader-key prefixes show a which-key popup (helix's `Space-` menu is the gold standard)
4. Command palette (`Ctrl+P`) — every action with a binding should also be a palette command
5. Documentation as the last resort, not the first

**Modal vs modeless** is a real choice. Modal apps (vim, helix, k9s ex-mode) get denser keybindings and need persistent mode indicators (status-bar color or label) plus distinct cursor shapes. Modeless apps (Textual, Bubble Tea, btop) lean on widget focus. Both are valid; pick one paradigm and stick with it.

**Mouse support** is contested. The pragmatic answer: support mouse where it's natural (clicking a tab, scrolling a list, focusing a pane) but require nothing of it. Every mouse-reachable target needs a keyboard equivalent. Note that mouse capture disables terminal text-selection — most emulators bypass with Shift.

## The non-negotiables (terminal hygiene)

These four are the difference between an app that feels professional and one that doesn't:

1. **Use the alternate screen for full-screen TUIs.** Don't pollute the user's scrollback. On exit, the terminal returns to where it was.
2. **Always restore terminal state on exit — even on panic.** Install panic/atexit handlers that disable raw mode, leave alt screen, and restore the cursor *before* printing the trace. A panicking TUI that leaves raw mode + alt screen is the worst possible UX. Ratatui's `color_eyre` integration, Bubble Tea's `defer p.RestoreTerminal()`, Textual's exception cleanup, Ink's `unmount()` all do this.
3. **Handle resize (`SIGWINCH`).** Re-layout on every resize event; debounce rapid resizes. Define a minimum size (typically 80×24) and render a clear "terminal too small" message rather than crash. Use percentages, `fr` units, `min`/`max`, and ratios — never absolute positions.
4. **Handle suspend (`Ctrl+Z` / `SIGTSTP`).** On suspend: disable raw mode, leave alt screen, restore cursor, then `kill(0, SIGTSTP)`. On `SIGCONT`: re-enter alt screen and force a full redraw. Windows lacks SIGTSTP; that's fine.

Other essentials:

- **Never block the UI thread on I/O.** All network/disk/subprocess work happens in goroutines/tasks/promises; results flow back via messages/channels/events.
- **Don't redraw on a fixed timer.** Redraw on events. Most apps idle at 0 fps until something happens. Cap animations at 30–60 fps.
- **Logging can't go to stdout.** Alt-screen + raw mode would corrupt the UI. Log to a file (`tea.LogToFile`, `~/.cache/myapp/log`), use a separate console (Textual's `textual console`), or render an in-app log pane (lazygit, k9s).
- **Cell width ≠ string length.** CJK ideographs are width 2; emoji should be width 2 (legacy `wcwidth` lies). Use `unicode-segmentation` (Rust), `golang.org/x/text` + `mattn/go-runewidth` (Go), `wcwidth` (Python), `string-width` (JS — Ink uses this) — never `len()` or `.length`.
- **Clipboard, hyperlinks, and desktop notifications go through OSC escapes** (52 / 8 / 9) — the *local* emulator interprets them, so they work over SSH where shelling out to `pbcopy`/`xclip` can't. Support matrices and tmux caveats: `references/interaction-patterns.md` → *Talking to the terminal emulator*.

## Testing and debugging

TUIs are testable; teams that skip tests usually just don't know the shape. Three layers, bottom-heavy:

1. **Unit-test the update/event layer as pure functions.** Every modern framework separates state change from rendering — feed a synthetic key event in, assert on state out. Cheapest, least flaky, and catches the "Tab silently stopped working" class of regression. Even Charm's own apps lean on this layer over harnesses.
2. **Golden/snapshot the rendered frame** at a *pinned terminal size and color profile* — unpinned size or profile is the #1 cause of snapshot tests that flap in CI. Harnesses: teatest/v2 golden files (Go), `TestBackend` + insta (Rust), Pilot + pytest-textual-snapshot (Python), ink-testing-library frame assertions (TS).
3. **PTY end-to-end sparingly** — one or two smoke flows at most; it's slow and the tooling is thin in every ecosystem.

Debugging follows one rule: **never write debug output to the terminal the TUI owns** — raw mode + alt screen turn `print` into screen corruption. Log to a file and `tail -f` it in a second terminal, or use the framework's dev console. Exact APIs live in each ecosystem reference's Testing / Debugging sections.

## Performance and compatibility

**Truecolor is now safe to assume** in 2026. Detect via `$COLORTERM=truecolor`; fall back to 256 then 16 then monochrome. The Kitty keyboard protocol (CSI u) is supported by kitty, foot, WezTerm, Alacritty, iTerm2, Ghostty, Rio, and Windows Terminal — opt-in for advanced bindings (Ctrl+I distinct from Tab, Shift+Enter distinct from Enter), always with legacy fallback.

**SSH and tmux** strip features unless explicitly enabled. For tmux:
```
set -ga terminal-overrides ",*:Tc"            # truecolor passthrough
set -g extended-keys on                        # CSI u
set -g extended-keys-format csi-u
set -g allow-passthrough on                    # kitty graphics
set -g mouse on                                # mouse forwarding
set -g set-clipboard on                        # OSC 52 clipboard
```

**Image protocols are fragmented**: kitty graphics (best quality) → Sixel (broadest compat) → iTerm2 inline. yazi auto-detects and supports all three.

## Accessibility — the honest take

TUIs are inherently inaccessible to screen readers. NVDA, JAWS, VoiceOver, and Orca read the visible buffer like a textbox, with no concept of widgets or focus. Best current practices when accessibility matters:

- Linear left-to-right, top-to-bottom layouts where possible.
- Never color-alone signals; pair with words (`[ERROR]`, `[OK]`, `[!]`).
- Full keyboard parity — every action reachable via keyboard.
- Provide a `--no-tui` plain mode that just prints output linearly.
- For Python/Textual specifically, `textual serve` → HTML is currently the best a11y route — same code runs in a browser, where real accessibility tooling exists.

If a11y matters seriously, ship a web alternative or a plain-CLI mode alongside the TUI. Don't pretend the TUI alone is accessible.

## Theming

Most production TUIs support themes via TOML/YAML config (lazygit, bottom, btop, helix, delta, bat, fzf), TCSS files (Textual), or composable styles (Lipgloss). Light/dark detection via OSC `]11;?` query or `$COLORFGBG`; Lipgloss's `LightDark` and Textual's runtime theme switching are the cleanest implementations.

Community palettes you should be able to support: Catppuccin (Latte/Frappé/Macchiato/Mocha), Dracula, Nord, Gruvbox, Tokyo Night, Rose Pine, Solarized, base16. Build your theme via semantic tokens, then map tokens → palette colors. Adding a new theme should be one config file, not a code change.

## Patterns worth naming

Refer users to these by name when you spot them:

- **The fzf pattern** — instant fuzzy filter as core interaction. Filter must be sub-100ms; show result count; offer `--exact`; `--preview` pane; `Tab` for multi-select. Used by fzf, skim, telescope.nvim, atuin, zoxide, helix, Textual command palette.
- **The lazygit pattern** — multi-pane with numeric tab navigation. 5+ panels, `1-5` jumps, `Tab` cycles, single letters trigger panel-specific actions, context-sensitive footer. Trade-off: cognitive load — `c` does different things in each panel.
- **The k9s pattern** — command-driven via vim-style ex-commands (`:pods`, `:nodes`, `:svc`) with tab-completion and aliases. Fast for power users; demands tab-completion or aliases listing for discovery.
- **The helix pattern** — selection-first modal editing (select-then-act vs vim's act-on-motion); multi-cursor as primary; Tree-sitter integration; `Space` opens which-key popup.
- **The miller-columns pattern** — three columns (parent / current / preview), `h` ascend, `l` descend. ranger, lf, nnn, yazi, broot.
- **The command palette pattern** — `Ctrl+P` modal with fuzzy-matched action list. Every action that has a binding should also be a palette command; show keybinding next to command name.
- **Dual product** — ship CLI + TUI from the same core. helix, atuin, posting, gh all do this. The CLI handles scripts; the TUI handles exploration.

For deeper coverage of any of these patterns and the specific apps that exemplify them, read `references/exemplar-apps.md`.

## Common pitfalls

Ranked by real-world complaint frequency:

1. **Hardcoded colors clashing with user themes.** Use semantic tokens.
2. **Crash on resize.** Subscribe to `SIGWINCH`; debounce; never assume fixed dimensions.
3. **Blocking the UI thread on I/O.** Async everything.
4. **Color-only signaling.** Add letters or symbols.
5. **Unicode glyphs failing on minimal SSH or Windows conhost.** Provide ASCII fallback.
6. **Polluting scrollback.** Use the alternate screen.
7. **Binding terminal-reserved keys** (Ctrl+C, Ctrl+Z, Ctrl+S/Q).
8. **Wall-of-shortcuts with no progressive disclosure.** Footer → `?` → palette.
9. **Inconsistent spatial layout** (panels reordering on focus). Don't.
10. **Misaligned tables** when text contains CJK or emoji. Use cell-width libraries.

## Decision flow for new TUI/CLI projects

When the user asks you to build something:

1. **Is this a one-shot command, a summon-choose-exit tool, or a full-screen app?**
   - One-shot CLI (no UI, exits when done) → load `references/cli-basics.md`. Apply argparse + color + maybe a spinner and you're done.
   - Summon–choose–exit tool (fzf-class picker, prompt, wizard, live progress) → render **inline**, not on the alt screen: bounded height, machine-readable result to stdout, a one-line receipt left in scrollback. See `references/visual-patterns.md` → *Inline, alt-screen, or overlay*.
   - Full-screen interactive (a session you live in) → alt screen; continue.

2. **What ecosystem?**
   - Already chosen → load that ecosystem's reference.
   - Not chosen → ask. Quick guide: Go for compiled binaries with great styling (Bubble Tea); Rust for performance and reliability (Ratatui); Python for rapid development with web-deploy option (Textual); TS/JS for npm distribution and React-familiar teams (Ink).

3. **What's the workflow shape?** Match to one of the seven canonical layouts above before writing any code. Sketch the panels in ASCII first.

4. **What are the 5–8 most common actions?** Those become the always-visible footer hints. Everything else lives behind `?` or the command palette.

5. **What's the data model?** Lists, trees, tables, forms, free-text? This determines which widgets you need and whether to virtualize.

6. **What's the responsive plan across sizes?** Don't design for one window. Walk the breakpoint ladder (wide >120 / standard 80–120 / narrow 60–80 / too-small below) and decide what gets hidden, collapsed, or stacked at each — and the "terminal too small" message below the 80×24 floor. A fixed grid that can't fold to a single pane is a design smell; drill-down degrades more gracefully. See `references/visual-patterns.md` → *Responsive design*.

Then, with the ecosystem reference loaded, write the code. The non-negotiables (alt screen, terminal restoration, resize, suspend, async I/O, no UI-thread blocking) apply regardless of language.

## When reviewing or refactoring an existing TUI

Walk through this checklist:

- Does it use the alternate screen? Does it restore terminal state on panic?
- Does it handle resize and suspend?
- Are colors semantic tokens, or hardcoded? Is `NO_COLOR` honored?
- Is the app usable in monochrome (color removed, layout still readable)?
- Are there always-visible footer hints? Does `?` show full help?
- Is every action keyboard-reachable? Are `q` and `Esc` consistent?
- Are panels in fixed positions? Or do they jump around on focus?
- **Clutter audit** — border-nesting depth (>1 inside a panel?), duplicate signals encoding one state, markers on every row, chrome-vs-data ratio. Name specific cuts, not "simplify."
- **Pressure-test the floor** — what does this do at 80×24 and a 60-col tmux split? Is there a degradation plan (what hides / collapses / stacks) and a "too small" message? Flag this even if the user didn't ask about size.
- Are tables aligned correctly? Do they handle CJK / emoji width?
- Are long lists virtualized?
- Does I/O block the UI thread anywhere?
- Are reserved keys (Ctrl+C/Z/S/Q) bound to anything?
- Does it ship with at least one popular community theme support (Catppuccin, Gruvbox, etc.) or a way to define one?
- Is the update/event layer unit-testable as pure functions? Are frame snapshots (if any) pinned to a size and color profile?

Most existing TUIs fail 3–5 of these. Calling them out specifically gives the user a concrete improvement path.

---

## Style of help to give

When the user asks "should I do X or Y?" — give a recommendation. The terminal renaissance has produced enough convergent design that many questions have a clear best answer (use the alternate screen, support `hjkl`+arrows, honor `NO_COLOR`, use semantic color tokens). Don't hedge on settled questions. Hedge on real tradeoffs (modal vs modeless, mouse support, single-key destructive actions vs always-confirm).

When showing code, prefer the idiom of the chosen ecosystem — don't translate Bubble Tea's MVU into Ratatui's immediate-mode and call it good. Each ecosystem has converged on a style; meet it where it is. The reference files document each one in detail.

When the user is stuck on a design decision, point at an exemplar app that solved the same problem (`references/exemplar-apps.md`) — concrete examples beat abstract principles for design questions.
