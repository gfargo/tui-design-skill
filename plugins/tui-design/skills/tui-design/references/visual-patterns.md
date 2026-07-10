# Visual patterns — borders, color, density, layout

A deep dive into the visual design choices that make TUIs feel professional. The top-level `SKILL.md` covers the principles; this file goes deeper with the *why*, the *when*, and the trade-offs.

**Contents:**
- [The seven canonical layouts in detail](#the-seven-canonical-layouts-in-detail)
- [Inline, alt-screen, or overlay — where the UI lives](#inline-alt-screen-or-overlay--where-the-ui-lives)
- [Borders — when, what, and why](#borders--when-what-and-why)
- [Color in depth](#color-in-depth)
- [Typography in monospace](#typography-in-monospace)
- [Density: pack vs pad](#density-pack-vs-pad) (includes the clutter audit)
- [Responsive design — breakpoints and the floor](#responsive-design--breakpoints-and-the-floor)
- [Visual hierarchy in monospace](#visual-hierarchy-in-monospace)
- [Tables and lists](#tables-and-lists)
- [Status bars, headers, footers](#status-bars-headers-footers)
- [Progress indicators](#progress-indicators) (includes disconnected/stale-data and timeout/cancel UX)
- [Theming systems](#theming-systems) (includes [icons and Nerd Fonts](#icons-and-nerd-fonts--there-is-no-detection-only-opt-in))
- [Common visual pitfalls](#common-visual-pitfalls)

---

## The seven canonical layouts in detail

### 1. Persistent multi-panel

All panels visible simultaneously in fixed positions. Focus shifts via Tab or numeric keys. The user builds spatial memory: "files are top-left, branches are below, diff is on the right."

**Examples:** lazygit (5 left panels + 1 right), btop (CPU/mem/net/processes as 4 quadrants), htop (header / process list / F-key footer).

**When to use:**
- Users want to see multiple related views at once without switching.
- The data is observed at a glance (monitors, dashboards).
- Numeric panel jumps make sense (`1`–`5`).

**When to avoid:**
- Each pane needs full attention (use IDE three-panel or drill-down stack instead).
- Total information would overwhelm at smaller terminal sizes.

**Implementation notes:**
- Use border *color* to indicate the focused panel — strongest possible signal.
- Footer hint bar should be **panel-aware**: `c` does different things in lazygit's Files vs Commits panel; show what's relevant.
- Numeric jumps (`1`–`5`) should work from any panel — don't make users return to a "menu" first.

### 2. Miller columns

Three (sometimes more) columns: parent → current → preview. `h`/`l` (or `←`/`→`) ascend/descend.

**Examples:** yazi (default ratio `[1, 4, 3]` for parent/current/preview), ranger (the original), broot (tree-mode variant), nnn, lf.

**When to use:**
- Hierarchical data: filesystems, JSON, K8s resource trees.
- Users need to see context (parent) and outcome (preview) without losing position.

**When to avoid:**
- Narrow terminals (<80 cols) — degrades poorly. Provide a single-pane fallback.
- Non-hierarchical data — the parent column is wasted.

**Implementation notes:**
- The middle column should be widest — that's where the user works.
- Preview column shows file content / nested object / pod logs depending on what's selected.
- Selection in the middle column updates the preview live (debounce if expensive).

### 3. Drill-down stack

Browser-style: navigate into deeper views with a back-stack, `Esc` returns to the previous view.

**Examples:** k9s (`:pods` → Enter on pod → `Esc` back), lazydocker (sidebar → drill into container → `Esc`), gh dash (PR list → PR detail).

**When to use:**
- Many resource types where the user needs to pivot between them.
- Each detail view is full-screen and demands attention.
- Command-mode navigation is natural (`:resource`).

**When to avoid:**
- Users need to compare two things side-by-side (use multi-panel).
- The back-stack would get deep (>3 levels confuses users).

**Implementation notes:**
- Status bar should show the current "address" (breadcrumb): `cluster/namespace/pods/my-pod-7d9f`.
- `Esc` always backs up one level. The user should never feel trapped.
- Implement a stack of view-state objects. On push, save the current view; on pop, restore.

### 4. Widget dashboard

Independent widgets in a grid, each owning its data lifecycle. Layout is configurable.

**Examples:** bottom (btm), btop, glances, gtop. All let users define rows and column ratios in TOML.

**When to use:**
- Monitoring/observability where users want to compose their own view.
- Each widget has its own update cadence.

**When to avoid:**
- Static data layouts — config overhead doesn't earn its keep.
- Users who want a single curated experience.

**Implementation notes:**
- Define a config schema (TOML/YAML) early. Users *will* want to customize.
- Each widget should be independently scrollable/expandable.
- Mouse-resize is nice-to-have (btop supports it).

### 5. IDE three-panel

Sidebar → main content → detail/output. The main panel often has tabs giving it multiple personalities.

**Examples:** Posting (collection tree → request editor → response), Harlequin (catalog → editor → results), helix (file explorer + built-in pickers + diagnostics).

**When to use:**
- Editor-like workflows where users compose then execute then inspect.
- A small set of "current items" needs prominent focus while keeping a navigator.

**When to avoid:**
- Pure browsing (no composition step) — multi-panel is simpler.
- Mobile-style narrow terminals — too many panels to fit.

**Implementation notes:**
- Sidebar collapsible (`Ctrl+B` or similar). Users will toggle it.
- Main panel tabs cycled with `[`/`]` or `Ctrl+Tab`.
- Output panel often docked bottom or right; resizable.

### 6. Overlay / popup

Appears over the shell, does one thing, exits.

**Examples:** fzf (the canonical example), atuin (replaces Ctrl+R), zoxide+fzf for directory selection, gum prompts.

**When to use:**
- "Summon → choose → output → exit" interactions.
- Tools meant to compose with shell pipelines.
- Replacing a built-in like Ctrl+R reverse-search.

**When to avoid:**
- Long-running interactions — users will resent the cramped popup space.
- Anything that needs to persist state between invocations.

**Implementation notes:**
- Buffer choice (inline vs alt screen) and the exit contract are covered in full below — see *Inline, alt-screen, or overlay*.
- Sub-100ms startup is non-negotiable — users summon these dozens of times a day.

### 7. Tabbed within panel

Tab bars inside a larger layout, cycled with `[`/`]` or `Ctrl+Tab`.

**Examples:** lazygit's Local/Remotes/Tags tabs in the branches panel; lazydocker's Logs/Stats/Env/Config/Top tabs in the right pane.

**When to use:**
- One panel needs multiple personalities without changing the global layout.
- The tabs are related (different views of the same selected object).

**When to avoid:**
- Tabs are unrelated — that's a sign you actually need different panels.
- More than 5–6 tabs — split into nested tabs or use a different pattern.

**Implementation notes:**
- Active tab visually distinct (bold + underline + accent color).
- Tab key labels (`Logs [1]`, `Stats [2]`, `Env [3]`) so users can jump directly.
- Cycle order matches reading order (left to right).

---

## Inline, alt-screen, or overlay — where the UI lives

Before choosing a layout, choose a screen buffer. The **alternate screen** is a separate buffer with no scrollback; on exit the terminal restores whatever was there before. **Inline** rendering paints in the normal buffer, below the shell prompt, and scrolls with everything else.

**The rule: alt screen for apps you *live in*; inline for tools you *summon*.** Editors, file managers, dashboards — long-lived, navigational, full-screen — belong on the alt screen precisely so they don't pollute scrollback (vim's reason for using it). One-shot pickers, prompts, confirmations, and progress for a single command belong inline. Scrollback is the user's working memory: taking over the whole screen — erasing their context — to pick one item from a list is rude. An inline tool behaves like a command, not an application.

### Mechanics per framework

- **Bubble Tea v2** — inline is the default. Alt screen is a declarative field on the view: `v := tea.NewView(...); v.AltScreen = true`. Because it's set per-frame, an app can switch between inline and alt-screen at runtime.
- **Ink** — inline by default. Since Ink 7, the `alternateScreen: true` render option gives a vim-style alt screen that restores the previous terminal content on exit (interactive mode only — ignored in CI or with piped stdout).
- **Textual** — `app.run(inline=True)` (since 0.55). Height is controlled with CSS on `Screen`: `Screen { &:inline { height: 50vh; } }`. Inline mode is not supported on Windows.
- **Ratatui** — `Viewport::Inline(height)` via `Terminal::with_options`. To emit permanent log/output lines above the live UI, `Terminal::insert_before` is the sanctioned pattern: inserted lines push the viewport down, then scroll into scrollback above it.

### The fzf model — bounded inline viewport

`fzf --height 40%` renders the finder below the cursor instead of taking the full screen. The UI paints on `/dev/tty` (stderr as fallback) so stdout stays clean — that's why `vim $(fzf)` works. This hybrid — inline, height-capped, scrollback intact above — is the right shape for anything fzf-like.

### The exit contract — the receipt pattern

Inside `$(...)` or a pipe, stdout is not a TTY; anything the UI paints to stdout becomes part of the captured "result." So: **chrome to stderr or `/dev/tty`, answer to stdout.** gum runs its Bubble Tea UI with `tea.WithOutput(os.Stderr)` and prints the chosen value to stdout, stripping ANSI when stdout isn't a TTY — which is exactly why `CHOICE=$(gum choose a b c)` composes.

On exit, do one of two respectable things: erase the transient UI completely (fzf's default), or replace it with a one-line receipt that stays in scrollback — `✓ deployed api-server in 12s`. Textual's `inline_no_clear` and fzf's `--no-clear` are the deliberate leave-the-last-frame escape hatches. What you must not do is leave a dead, half-drawn UI behind.

### Choose by workflow

| Workflow | Mode |
|---|---|
| One-shot pick / confirm / progress | Inline; exit with a receipt |
| Explore / monitor / edit session | Alt screen; restore on exit |
| Hybrid (fzf-like; logs + live status) | Inline with a height cap (`--height 40%`, `Viewport::Inline`) |

---

## Borders — when, what, and why

### The Unicode block

The Unicode box-drawing block is U+2500–U+257F:
- **Single line**: `─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼`
- **Heavy**: `━ ┃ ┏ ┓ ┗ ┛ ┣ ┫ ┳ ┻ ╋`
- **Double**: `═ ║ ╔ ╗ ╚ ╝ ╠ ╣ ╦ ╩ ╬`
- **Rounded**: `╭ ╮ ╰ ╯` (combined with single-line straights)

### The aesthetic landscape

- **Single-line** — default for most modern TUIs (lazygit, k9s, btop, htop). Reads cleanly without dominating.
- **Rounded corners** — the Charm aesthetic (Bubble Tea apps, gum, glow). Slightly softer; modern.
- **Heavy** — emphasis. Use sparingly — for the focused panel border, or a "hot" warning state.
- **Double** — reads as "DOS." Avoid for modern apps unless you're going for retro.

### When to use borders

- The pane has dynamic content needing a visible boundary.
- Focus state must be communicated visually (border color change is the strongest signal).
- Adjacent panels need clear separation.
- The border is doing real work — not just decoration.

### When to skip borders

- Content is static (htop has no internal borders — it's all dense layout).
- Density matters more than structure.
- The pane is implicitly bounded (only thing on screen, or at the edge).

Don't decorate — whitespace is usually separator enough (see *The clutter audit* below).

### The background-leak problem

Each terminal cell has only fg/bg colors. A border cell renders the line in the foreground but the cell's background "leaks" through behind the border characters. If your panel has a contrasting background to its parent, this looks wrong:

```
parent_bg has black background
panel has dark blue background
border characters: render in panel's blue background
        ^^^ creates a visible "step" between border and content
```

**Solutions:**
- Use the same background for panel and borders.
- Or use one-eighth block characters (`▏▎▍`) as borders — Textual does this for themed apps.

### ASCII fallback

For legacy SSH, Windows conhost, `TERM=dumb`, or any system where Unicode might be unreliable:
- Single-line `─│┌┐└┘├┤┬┴┼` → `-|+++++++++`
- Heavy → `=|+++` (or just bold the ASCII)
- Rounded `╭╮╰╯` → `+`

Detect via `$LANG` containing UTF-8 or `$LC_ALL`, and via terminal capability queries. Provide a config option (`--ascii`, `MYAPP_ASCII=1`) for explicit override.

---

## Color in depth

### The three tiers

Design in the three layers SKILL.md's *Color as a semantic system* names (monochrome / 16 ANSI / 256-truecolor). The depth worth adding here: the user's terminal theme is sacred. The 16 ANSI colors are *theme variables* — the user's `red` might be `#ef5350` (Material), `#dc322f` (Solarized), or `#f38ba8` (Catppuccin). You design in terms of "red means error," not "use #ff0000 for errors."

### Semantic tokens

Define a vocabulary by *function*, not appearance:

```
status.success    → green
status.warning    → yellow
status.error      → red
status.info       → blue or cyan

text.primary      → default fg
text.muted        → dim or gray
text.emphasis     → bold + accent

bg.base           → default bg
bg.surface        → slightly elevated
bg.overlay        → modal/popup bg

accent.primary    → brand color
accent.secondary  → complementary

border.default    → muted
border.focus      → accent.primary

git.staged        → green
git.modified      → yellow
git.untracked     → red or cyan
git.added         → green (foreground)
git.deleted       → red (foreground)
```

Then map tokens to palette colors. **Lipgloss's `AdaptiveColor`**, **Textual's CSS variables**, and **Ratatui's palette indirection** all implement this.

This indirection earns its keep when adding themes (Catppuccin Latte + Frappé + Macchiato + Mocha is one config file, not four code changes) or when supporting light/dark modes.

### Conventional meanings

| Color | Meaning |
|---|---|
| Green | Success, added, online, OK |
| Red | Error, deleted, danger, offline |
| Yellow | Warning, modified, pending, in-progress |
| Cyan / Blue | Info, paths, links, hints |
| Magenta | Special, highlights, attention without alarm |
| Dim / gray | Secondary, disabled, metadata, timestamps |
| Bold (any color) | Title, primary content, emphasis |

Stick to conventions. A green error message confuses everyone.

### Color and accessibility

About 8% of males have red-green color vision deficiency. Don't rely on color alone:

- Pair color with **letters**: lazygit shows file status as `M` (modified, yellow), `A` (added, green), `D` (deleted, red), `??` (untracked, cyan). Even if color is invisible, the letters carry meaning.
- Pair color with **symbols**: delta's `+` and `-` line prefixes work in monochrome.
- Pair color with **position**: errors at the end of output, success in a separate column.

**Safe color pairs for CVD:**
- Blue + orange.
- Blue + yellow.
- Black + white (and any high-contrast neutral pair).

Avoid red + green as the only distinction. If you must use them, add letters or symbols.

### Honor `NO_COLOR`

[no-color.org](https://no-color.org) is a 2018 informal standard. Respect it: when `NO_COLOR` env var is set (any value), suppress all color output.

`ripgrep`, `bat`, `eza`, `delta`, `fd`, `gh`, `cargo`, all major modern tools honor it. Most language ecosystems' color libraries (chalk, picocolors, owo-colors, rich, lipgloss) handle it automatically.

Provide tool-specific `MYAPP_NO_COLOR` and `MYAPP_FORCE_COLOR` for finer control.

---

## Typography in monospace

You can't change font size. Typography signals are limited but useful:

| Attribute | Use for | Notes |
|---|---|---|
| **Bold** | Titles, current selection, primary content, focused panel name | Universal support |
| **Dim** | Metadata, timestamps, disabled items, secondary text | Universal support |
| **Italic** | Light emphasis | Poorly supported; never the only signal |
| **Underline** | OSC 8 hyperlinks, shortcut hints | Wide support; meaningful |
| **Reverse video** | Cursor row, current selection | Works on every terminal back to VT100 |
| **Strikethrough** | Cancelled / deleted items | Limited support |
| **Blink** | Don't | Disabled in most modern terminals; accessibility hazard |

**Reverse video is the canonical "current selection" signal.** It's the most reliable and most readable. Use it for the highlighted row in lists, the current cell in tables, the cursor position.

**Bold + accent color** for the focused panel's title. Combined with border color change, that's unmistakable focus indication.

---

## Density: pack vs pad

You have a fixed grid. Two strategies:

### Pack (high density)

Examples: htop, btop, k9s.

Used when:
- Data is scanned at a glance.
- It updates in real time.
- Users read horizontally across rows.

Tactics:
- Tight rows (no extra spacing).
- Compact headers (one line, dim text).
- Abbreviations and units (`GiB`, `1.2k`, `99.9%`).
- Sparklines, mini-bars.
- One-line per record.

### Pad (low density)

Examples: gum/huh forms, glow markdown, Posting.

Used when:
- Users are reading prose.
- Filling forms (fields need breathing room).
- Making single decisions.

Tactics:
- Generous vertical spacing between fields.
- One field per line; labels above for narrow.
- Single column for forms.
- Lots of margin around modals.

For separation in moderate-density layouts, reach for whitespace before borders (see *The clutter audit* below).

### Hybrid: hierarchy through density

Use density to communicate hierarchy: dense data tables in the main panel, padded settings/forms in modals, dense status bars at the bottom.

### The clutter audit — making "feels busy" countable

"It feels noisy" is a real signal but useless until you convert it into specific offenders. When a layout feels cluttered, **count — don't squint** — and report the count, not a vibe:

- **Border-nesting depth.** Trace any corner from the terminal edge inward. More than *one* border between the edge and the content is too many. A border wrapping content that's already inside a bordered panel separates nothing and shows no focus — delete it. Boxes-inside-boxes is the single most common cause of "busy," and an outer full-screen frame is almost always redundant (the terminal edge already frames the app).
- **Signals per piece of state.** Count how many things encode the same fact. `[PASS]` + green + `✅` + a `▶` row prefix is *four* signals for one status. Keep one (color paired with a letter/word for monochrome safety); cut the rest.
- **Always-on markers.** A glyph that appears on 100% of rows (a `▶` on every line) marks nothing — it's texture, not information. Reserve markers for the exception: the selected row, the failed item.
- **Chrome-to-data ratio.** Add up the cells spent on borders, titles, padding, labels, and repeated boilerplate (a full ISO date on every log line when only the time changes) versus cells showing actual data. A high chrome ratio *is* the cluttered feeling.
- **The removal test.** For each decorative element ask: "if I delete this, do I lose information?" If no, delete it. Whitespace is not empty space — it's the cheapest separator you have, and a single blank row routinely out-reads a heavy border.

Run this pass on any layout — yours or someone else's. "Three concentric borders before the content, status encoded four ways, a marker on every row, full datestamps repeated every log line" tells the user exactly what to cut. "Simplify it" tells them nothing.

---

## Responsive design — breakpoints and the floor

A terminal layout is not designed for one size. The same app runs on a 220-column ultrawide, an 80×24 SSH session, a 60-column tmux split, and a 13-inch laptop. **A layout that only works at the author's window size is unfinished** — and the author rarely notices, because they only ever see their own terminal. Pressure-test every layout at the floor, and raise it in any review even when the user only asked about something else: it's the most-missed issue in TUI design.

### The breakpoint ladder

Decide behavior per width band, widest to narrowest. Exact thresholds depend on content, but the shape is universal:

- **Wide (>120 cols)** — the full multi-panel layout; you can afford a side panel or preview alongside the primary view.
- **Standard (80–120)** — the baseline most users see. Often: one primary view full-width, with details/logs on drill-in (Enter / a key) rather than permanently side-by-side.
- **Narrow (60–80)** — collapse to a single column. Stack panels vertically or hide all but the primary. Multi-column layouts (Miller columns, 2×N grids) **must** fold to one pane here. (lazygit's `--screen-mode full` is a related single-panel mode — but it's a user-selectable escape hatch, not automatic responsive behavior.)
- **Too small (<60 cols or <24 rows)** — don't render garbage or panic. Show a clean `terminal too small — need 80×24` message until the user resizes.

This is why a **drill-down model degrades better than a fixed grid**: when only one primary thing is ever on screen, narrowing just shrinks it; a fixed 2×2 grid has nowhere to go and turns to mush. If you find yourself unable to make a grid responsive, that's often a sign the layout should have been drill-down in the first place.

### Mechanics

- **Lay out in relative units, never absolute positions:** percentages (Textual `width: 30%`), ratios (Ratatui `Ratio(num, den)`), `Min`/`Max`/`Fill` constraints (Ratatui), `fr` units (Textual `1fr`/`3fr`), flex (Ink/Yoga). Recompute the layout from the current frame size on every render — never cache pixel positions.
- **Decide what's load-bearing.** When width runs out, what hides *first*? Usually: preview pane → secondary columns → low-priority table columns. Keep the primary view and the footer hints. **Detail-on-Enter** is the escape hatch — it lets you hide columns/fields at narrow widths without losing access to the data.
- **Truncate, don't wrap, in cells**; reserve a cell for the ellipsis. Tail-truncate paths, middle-truncate when the basename matters.
- **Handle `SIGWINCH`** and re-layout on every resize, debounced (100–200ms) so dragging a tmux divider doesn't thrash.
- **Define the minimum size explicitly** (80×24 is the conventional floor) and *test there* — not just at your own resolution. `tmux split-window -h` is a free narrow-terminal test rig.

When reviewing a layout, state the degradation plan concretely: "at 80×24 the preview drops and you get parent│current; below 60 it's a single pane; below that, a too-small message." **A review that doesn't name what happens at the floor hasn't finished.**

---

## Visual hierarchy in monospace

Since you can't change font size, hierarchy comes from:

1. **Position** — top/left reads first; status bar at bottom.
2. **Color and weight** — bold + accent for headlines; dim for secondary.
3. **Reverse video** — current selection.
4. **Indentation and connectors** — `├─ └─` for trees; consistent indent units (2 cells is standard).
5. **Whitespace** — blank rows for separation; pads around important content.
6. **Bullets / symbols** — `▶` expandable, `▼` expanded, `●` active, `○` inactive, `•` static bullet.
7. **Borders** — focused panel highlighted via border color.

Combining 2–3 signals creates clear hierarchy. The current selection: reverse video + bold. The focused panel: accent border + bold title. A warning: yellow + `[!]` prefix + slightly lifted from surrounding text via blank line above.

---

## Tables and lists

### Alignment rules

- **Numerics: right-aligned.** Easy to scan magnitudes.
- **Text: left-aligned.** Standard.
- **Dates: fixed-width ISO-8601** (`2026-04-28 14:30`). Sortable; doesn't shift on locale.
- **Status / categorical: centered or left** — be consistent.

### Truncation

When content exceeds column width:

- **Tail truncation** (`/usr/local/share/...`) — for paths, where the tail is the leaf you're looking at. Used by eza, k9s.
- **Middle truncation** (`/usr/.../file.txt`) — when the basename matters. Used by bat, helix.
- **Wrap** — only for prose. Never wrap in cells of dense tables.

Reserve a cell (or three for `...`) for the ellipsis. Don't truncate so aggressively that nothing remains: `... ` is useless.

### Sort indicators

Show which column is currently sorted: `▲` ascending, `▼` descending. Place after the column header: `Size ▼`. Click (or key) to toggle and cycle.

### Filtering

When filtering a list:

- Show count: `123/45678` (the fzf convention).
- Highlight matched substring within results.
- Sub-100ms response — anything slower feels broken.

### Wide tables on narrow terminals

Three approaches:

1. **Hide low-priority columns.** Define column priority; drop them as width shrinks. eza does this.
2. **Horizontal scroll.** k9s scrolls table content horizontally on narrow terminals.
3. **Detail-on-Enter.** Pressing Enter on a row opens a side panel or modal showing all fields. The universal escape hatch.

Detail-on-Enter is the highest-leverage pattern: you can show fewer columns, and the user is one keypress away from full detail.

### Virtualization

**Always virtualize** lists that might exceed a few hundred items.

- **k9s** virtualizes for thousands of pods.
- **Toolong** tails multi-GB log files.
- **Textual `DataTable`** virtualizes by default.
- **Ratatui `List` + `ListState`** handles offsetting efficiently.
- **Bubbles `list`** virtualizes.
- **Ink** + `<Static>` for append-only logs.

The naive "render all rows, scroll viewport" approach degrades horribly at 10k+ items.

---

## Status bars, headers, footers

### The canonical four-section layout

```
┌─────────────────────────────────────────┐
│ Header (top)                            │ ← persistent context: app, dataset, mode
├─────────────────────────────────────────┤
│                                         │
│   Main area (middle)                    │ ← the panels
│                                         │
├─────────────────────────────────────────┤
│ Status / mode line                      │ ← ephemeral feedback
│ Footer hint bar                         │ ← always-visible shortcuts
└─────────────────────────────────────────┘
```

Some apps merge status and footer into one line. Some skip the header. The principle stays: persistent context up top, work in the middle, keys at the bottom.

### Header content

- App name (often with logo char or color block).
- Current dataset / context: branch name (lazygit), cluster + namespace (k9s), file path (bat/glow).
- Mode indicator (NORMAL / INSERT in editors).
- Right-aligned: time, host, version (sparingly — only if meaningful).

### Status / mode line

- Ephemeral feedback: "Saved", "3 files changed", "Connecting...".
- Auto-fade after a few seconds (or replace with idle state).
- Vim-style mode indicators with **distinct cursor shapes**: block in NORMAL, bar in INSERT, underline in REPLACE.
- Color-coded: green = OK / saved, yellow = pending, red = error.

### Footer hint bar

Visual format: `key action · key action · key action`. Use `·` (middle dot) or `|` as separator. 3–5 shortcuts, updated per context (panel, mode).

Examples:
- htop: `F1Help F2Setup F3Search F4Filter F5Tree F6SortBy F7Nice- F8Nice+ F9Kill F10Quit`
- lazygit: per-pane, e.g., in Files panel `space stage ↵ commit p push P pull r refresh ?`

Why this bar matters and how to auto-generate it from your keymap: `references/interaction-patterns.md` → *Layer 1: Always-visible footer hints*.

---

## Progress indicators

### Spinners

The de facto modern default for indeterminate work: **Braille spinners**.

```
⠋⠙⠹⠸⠼⠴⠦⠧
```

Eight frames at ~80ms per frame = smooth rotation. `cli-spinners` (the npm package, vendored everywhere) ships ~70+ named styles.

**Rules:**
- Show only after ~150–200ms — instant work shouldn't flash a spinner.
- Stop with a final state symbol: `✓` (success), `✗` (failure), or just disappear.
- Suppress entirely on non-TTY. CI logs shouldn't have spinners.

### Determinate progress bars

Block characters for sub-cell precision:
```
▏▎▍▌▋▊▉█
```

These give 8 sub-positions per cell. A 40-cell-wide bar can represent 40 × 8 = 320 distinct progress states.

```
[████████▎             ] 41%
```

Show: percent, current/total counts where meaningful, ETA for long operations.

### Multi-progress

Multiple parallel tasks each with their own bar:

```
package-a [████████████████████] 100% ✓
package-b [████████▎           ]  41%
package-c [██▎                 ]  10%
```

indicatif `MultiProgress`, rich `Progress` (multiple tasks), and listr2 `concurrent` mode support this out of the box; Bubbles ships only a single `progress` component — compose multiple bars by hand. Used by Docker pulls, npm/cargo builds, parallel installers.

### Pulse / fade

Ambient indication of background work without commanding attention. Used by lazygit's auto-fetch — a subtle dim pulse on the relevant panel. Useful when work is happening but doesn't need to be in the user's face.

### Empty states and loading states

**Empty states:** never just "No data." Say what to do next: "No requests. Press `n` to create one." Posting does this well.

**Loading states:** skeleton text or "Loading..." with a delayed spinner (don't flash for sub-200ms loads). Animate only when something is happening.

**Error states:** what failed and how to recover. "Connection refused. Press `r` to retry."

**Disconnected/stale-data states, for anything backed by a live connection:** k9s ships real retry/backoff config for this (`apiServerTimeout`, `maxConnRetry`) — connection loss is a designed-for case, not an afterthought. Keeping the last-known-good view visible (dimmed, with a "stale" or "reconnecting" indicator) rather than blanking the screen is the reasonable approach and what the retry mechanics imply, though it's worth being honest that this exact visual treatment isn't independently documented anywhere — treat it as the sensible inference, not a cited standard. What *is* independently confirmed as a failure mode to avoid: btop has an open bug where a temporarily-unavailable GPU permanently rewrites the user's saved widget configuration instead of just hiding the metric until it reappears — a concrete example of *not* degrading gracefully. Don't let transient unavailability mutate persistent config.

**Timeout and cancellation for a hung operation:** worth doing — show elapsed time once a wait crosses a second or two, and let `Esc` cancel an in-flight request — but be aware this isn't an established convention you can point to; even lazygit and gh only have partial, inconsistently-applied versions of it (spinners without a documented cancel contract, progress meters added feature-by-feature rather than systemically). There's also no TUI-specific sourced number for "give up and show an error after N seconds" — if you need one, the general web-UI guidance (indicator at 1s, determinate indicator past 3s) is a reasonable default to borrow, but say so rather than presenting it as TUI precedent. Prioritize showing elapsed time and allowing cancellation over picking a specific auto-timeout.

---

## Theming systems

Most production TUIs support themes. The canonical approach:

1. **Define semantic tokens** (`status.error`, `text.muted`, etc.).
2. **Define palette mappings** as TOML/YAML/CSS — one file per theme.
3. **Allow theme selection** via config, env var, or runtime command.

### Configuration formats

- **TOML** — lazygit, bottom, btop, helix, delta, bat, fzf, starship.
- **YAML** — k9s, alacritty.
- **TCSS (Textual CSS)** — Textual apps; live-reloads.
- **JSON** — VS Code-style; less common in TUIs.

### Community palettes you should support

Either ship them or document how to import them:

- **Catppuccin** (Latte, Frappé, Macchiato, Mocha).
- **Dracula**.
- **Nord**.
- **Gruvbox** (light, dark; soft, medium, hard).
- **Tokyo Night**.
- **Rose Pine** (Main, Moon, Dawn).
- **Solarized** (light, dark).
- **base16** umbrella spec — many themes follow this.

The community has built theme repos for most popular tools; users expect plug-and-play.

### Icons and Nerd Fonts — there is no detection, only opt-in

No terminal emulator exposes "a Nerd Font is installed and active" as a queryable signal — not kitty, WezTerm, iTerm2, Alacritty, Windows Terminal, or Ghostty. Fonts are a client-side rendering concern the terminal protocol has no capability query for; even reading the configured font name from a config file (the one heuristic tool that tries this, `has-nerd-font`, does exactly that) doesn't guarantee the font is actually installed, and font-fallback chains mean a declared font can silently substitute per-glyph anyway. **Don't invent a detection scheme — gate icons behind an explicit opt-in instead**, the way real tools do:

- **eza** — `--icons=WHEN` (`always` / `automatic` / `never`); `automatic` gates on stdout being a TTY, not on font presence — it fully trusts the user.
- **lazygit** — `gui.nerdFontsVersion: '2' | '3' | ""`; empty (the default) means no icons at all.
- **yazi** — icons are default-on, baked into the shipped theme file rather than gated by a flag; a user without a Nerd Font swaps in a community `theme-no-nerd-fonts.toml` instead of toggling a setting.

**Pin the codepoint generation, not just "Nerd Font on/off."** Nerd Fonts v3 reorganized Material Design Icons' codepoints (`F500–FD46` → `F0001+`) because the old range collided with CJK Unicode — a real, documented breaking change, which is exactly why lazygit's config asks for `'2'` or `'3'` explicitly rather than shipping one hardcoded set.

The fallback ladder — Nerd Font glyphs → plain Unicode symbols → ASCII — is real, but starship is the cleanest evidence of a tool actually shipping all three rungs as named presets (`nerd-font` / `no-nerd-font` / `plain-text-symbols`). Most tools are binary (icons on with a Nerd Font, or off), not a full three-tier ladder — don't imply every icon-capable tool implements all three.

### Light/dark detection

- OSC `]11;?` query — many terminals respond with their background color.
- `$COLORFGBG` env var — set by some terminals (rxvt-derivatives).
- Lipgloss's `AdaptiveColor` and Textual's runtime theme switching abstract this.

If you support both light and dark, default to "auto" and let users override with `--theme dark`.

---

## Common visual pitfalls

1. **Hardcoded colors** that clash with user themes. Use semantic tokens.
2. **Decorative borders** that don't earn their keep.
3. **Color-only signaling.** Pair with letters or symbols.
4. **Misaligned tables** when text contains CJK or emoji. Use `unicode_width` / `string-width`.
5. **Over-bolding.** Bold loses meaning when half the screen is bold.
6. **Inconsistent capitalization** in headers (mix of "Branch", "branch", "BRANCH").
7. **Emoji as the only signal.** Some terminals render them as boxes.
8. **Light-mode-only colors** (low contrast on dark, or vice versa).
9. **Tiny status bar** that hides important state under the fold.
10. **No visual focus indication** — users tab around guessing where they are.

When reviewing a TUI, walk this list. Most existing apps fail on 3–5 items.
