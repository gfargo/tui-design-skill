# Interaction patterns — keybindings, focus, navigation, modal vs modeless

A deep dive into how users interact with TUIs — keybinding philosophy, focus management, navigation patterns, mouse support, and discoverability. The top-level `SKILL.md` covers the principles; this file goes deeper into the *why* and the trade-offs.

**Contents:**
- [Keybinding philosophies](#keybinding-philosophies)
- [Cross-app keybinding conventions](#cross-app-keybinding-conventions)
- [Reserved keys — never bind these](#reserved-keys--never-bind-these)
- [Discoverability — the four-layer pattern](#discoverability--the-four-layer-pattern)
- [Modal vs modeless — the deeper trade-off](#modal-vs-modeless--the-deeper-trade-off)
- [Focus management](#focus-management)
- [Search and filter](#search-and-filter)
- [Multi-select](#multi-select)
- [Mouse support — the real trade-off](#mouse-support--the-real-trade-off)
- [Undo / redo](#undo--redo) · [Confirmation patterns](#confirmation-patterns)
- [Talking to the terminal emulator — OSC 8, 52, 9](#talking-to-the-terminal-emulator--osc-8-52-9)
- Named patterns: [fzf](#the-fzf-pattern-in-detail) · [lazygit](#the-lazygit-pattern--multi-pane-with-numeric-tabs) · [k9s](#the-k9s-pattern--command-driven) · [helix](#the-helix-pattern--selection-first-modal-editing)
- [Common interaction pitfalls](#common-interaction-pitfalls)

---

## Keybinding philosophies

There are four major schools. Most apps blend them.

### 1. Vim-style (modal)

**Identity:** modes (NORMAL, INSERT, VISUAL, COMMAND), single-letter motions and operators in NORMAL mode, leader keys for namespaces.

**Examples:** vim, neovim, helix, kakoune, k9s (ex-mode), aerc, weechat (command mode).

**Strengths:**
- Densely expressive — `5dw` ("delete five words") is two operators applied to a count.
- Hands stay on home row; minimal modifier-key gymnastics.
- Power users get fast.

**Weaknesses:**
- Steep learning curve.
- "What mode am I in?" confusion if mode indicator is weak.
- Modal text input fights conventional editing (Ctrl+A, Ctrl+E, etc.).

**When to use:** editor-like tools where keystrokes are the primary interaction, users are likely to be vim-familiar, you want dense expressivity. Not appropriate for general-purpose tools targeting non-vim users.

### 2. Emacs-style (chord)

**Identity:** modifier-prefixed bindings (`C-x C-s` to save, `M-x` for command), no modes, deeply nested key tables.

**Examples:** emacs (the originator), readline-based shells, weechat (default), some bash bindings.

**Strengths:**
- No modes; what you press is what you get.
- Rich modifier space (`C-`, `M-`, `S-`, combinations).
- Discoverable with which-key.

**Weaknesses:**
- Modifier strain ("Emacs pinky").
- Conflicts with terminal-reserved keys.
- Less efficient than modal for repetitive editing.

**When to use:** rarely from scratch in 2026. Most Emacs-style apps inherit the convention from a long history. New apps usually go modal or modeless.

### 3. Arrow-key / GUI-like (modeless)

**Identity:** arrow keys + Enter + Tab + Esc + single-letter shortcuts. Mouse-first or mouse-friendly.

**Examples:** btop, htop (somewhat), fzf, gum, Posting, Harlequin, most modern Textual apps.

**Strengths:**
- Zero learning curve.
- Inclusive — works for users who've never touched vim.
- Pairs naturally with mouse support.

**Weaknesses:**
- Slower for power users.
- Less expressive — fewer keys means fewer commands.
- Modifier keys (Ctrl/Alt) for less-common actions.

**When to use:** general-purpose tools, dashboards, monitors, anything where you want broad usability.

### 4. Hybrid (modeless + vim motions)

**Identity:** support arrows AND `hjkl` simultaneously. Vim shortcuts as power-user paths but never required.

**Examples:** lazygit, k9s, yazi, gh dash, most modern TUIs.

**Strengths:**
- Best of both worlds — onboarding via arrows, speed via hjkl.
- Inclusive without sacrificing power.
- Familiar to users from many backgrounds.

**Weaknesses:**
- Slightly more code (handle both).
- Risk of inconsistency between which keys do what.

**When to use:** **default for new TUIs.** This has become the dominant pattern.

---

## Cross-app keybinding conventions

These have crystallized across the ecosystem. Use them unless you have a strong reason not to:

| Key | Action |
|---|---|
| `q` | quit |
| `?` | help |
| `/` | search / filter |
| `n` / `N` | next / prev match |
| `Esc` | cancel / back / dismiss |
| `Enter` / `Return` | confirm / drill in |
| `Space` | toggle / mark for multi-select |
| `:` | command mode |
| `gg` | top |
| `G` | bottom |
| `Tab` / `Shift+Tab` | switch focus |
| `r` | refresh |
| `1`–`9` | jump to panel / numbered tab |
| `hjkl` *and* arrows | move (support both) |
| `Ctrl+P` | command palette |
| `y` | yank / copy |
| `p` | paste / push |
| `d` | delete (often confirms first) |
| `e` | edit |
| `o` | open |

**Pick a paradigm and stay consistent.** Don't mix `Ctrl+S` and `:w` for save unless both clearly map to "write file."

---

## Reserved keys — never bind these

These belong to the terminal or shell:

| Key | Why |
|---|---|
| **Ctrl+C** | SIGINT — should always quit cleanly |
| **Ctrl+Z** | SIGTSTP — suspend; you must restore terminal state on resume |
| **Ctrl+\\** | SIGQUIT — abort with core dump |
| **Ctrl+S** / **Ctrl+Q** | XON/XOFF flow control on legacy serial terminals |

If you bind these, you'll get bug reports from users whose terminals freeze, can't suspend your app, or can't quit. The rare exception is `Ctrl+S` for "save" in editors (vim, helix) — but those editors traditionally disable XON/XOFF before binding.

Ctrl+H is sometimes Backspace, sometimes a free key — it depends on terminal config. Test before binding.

---

## Discoverability — the four-layer pattern

Every action a user can take should be discoverable through *at least one* of these layers, in order of immediacy:

### Layer 1: Always-visible footer hints

3–5 most-useful shortcuts, always visible at the bottom of the screen. Update based on context.

**This is the single most important discoverability tool.** Most users will never read your docs; they read the footer.

Examples:
- htop's F1–F10 strip.
- lazygit's per-pane hints (`space stage  ↵ commit  p push  P pull  r refresh  ?`).
- helix's status line.

Auto-generation is a force multiplier:
- **Bubble Tea**: `bubbles/help` reads from `key.KeyMap`.
- **Textual**: `Footer` widget renders `BINDINGS`.
- **Ratatui**: not auto-generated; build a helper that reads from your keybinding map.
- **Ink**: not auto-generated; build with `<Box>` + the same keymap source.

Define keys *once*, derive the footer.

### Layer 2: `?` help screen

Pressing `?` opens a modal or full-screen help with **all** keybindings, grouped by context.

This is universal — every TUI should have it. lazygit's `?` shows a categorized list of keys, with sections per panel. Textual's `?` (when implemented) typically shows a key table.

Format: `key  action  context`. Group by mode/panel/category.

### Layer 3: Leader-key / which-key

After pressing a leader (Space, `,`, `\`), show a popup with available follow-up keys. The user can:
- Read the list and pick.
- Type the key to dismiss the popup and trigger the action.
- Press Esc to cancel.

**The gold standard:** helix's `Space-` menu. Press Space, see `f` (file picker), `b` (buffer picker), `s` (symbols), `a` (LSP actions), etc. `which-key.nvim` is near-universal in neovim.

When to add: when your keymap exceeds ~20 distinct actions. Below that, `?` help is enough.

### Layer 4: Command palette

`Ctrl+P` (or similar) opens a fuzzy-matched action list. The user types to filter.

**The principle:** *every action that has a keybinding should also be a palette command.* The keybinding is the shortcut; the palette is the long-form name + searchable description.

Examples:
- Textual's built-in command palette (`Ctrl+P` by default since v0.77; it originally shipped on `Ctrl+\`, which collides with SIGQUIT).
- VS Code's Ctrl+Shift+P (the conceptual ancestor for many TUIs).
- helix's `:` (ex-style command, not strictly a palette but similar role).
- k9s's `:` (resource-typing, but adopts the same "type to filter actions" model).

Format each command:
```
Action name              keybinding
Description / context
```

Show the keybinding next to the command name — the palette doubles as keybinding documentation.

---

## Modal vs modeless — the deeper trade-off

### Modal (vim-style)

You're in a mode (NORMAL, INSERT, etc.). Keystrokes interpreted differently per mode.

**Requires:**
- Persistent mode indicator (status bar color or label).
- Distinct cursor shapes per mode (block in NORMAL, bar in INSERT, underline in REPLACE).
- A way to learn modes — usually a tutorial or readme.

**Trade-offs:**
- Pro: dense keybindings (no Ctrl/Alt needed for most operations).
- Pro: composable operators (`d` + motion = delete-by-motion).
- Con: confusion if mode is weakly indicated.
- Con: muscle memory required.

### Modeless

What you press is what you get. State changes happen via widget focus.

**Requires:**
- Clear focus indication (border color, reverse video on selection).
- Modifier-key bindings for less-common actions.

**Trade-offs:**
- Pro: zero learning curve.
- Pro: no mode confusion.
- Con: less expressive — limited by Ctrl/Alt combinations.
- Con: more visual real estate spent on focus indicators.

### The third option: contextual

Bindings change based on which panel is focused. Not "modes" in the vim sense — more like "the current panel determines what `c` means."

Examples: lazygit (`c` commits in Files, checks out in Branches, copies in Stash), k9s (panel-specific actions in addition to global ones).

This is **context-sensitive modeless** — works well if you have rich, panel-specific actions and a footer hint bar that shows what's available right now.

---

## Focus management

In a multi-panel TUI, **which panel has focus** determines:
- Which keystrokes the panel responds to.
- Which footer hints show.
- The visual highlight (border color, reverse video on selection).

### Focus indicators (in order of strength)

1. **Border color change** — strongest. The focused panel's border becomes the accent color.
2. **Border weight** — thin → thick. Subtle but works.
3. **Title color/weight** — bold + accent on focused panel title.
4. **Background tint** — subtle but be careful (background-leak issues with borders).
5. **Selection visible** — only the focused panel shows reverse-video selection; unfocused panels show muted selection.

Combine 2–3 of these for unambiguous indication.

### Focus navigation

| Method | Best for |
|---|---|
| **Tab / Shift+Tab** cycle | Linear panel order; small number of panels |
| **Numeric keys** (`1`–`9`) | Direct jumps; many panels (lazygit `1`–`5`, yazi `1`–`9`) |
| **Directional** (`Ctrl+w h/j/k/l` like vim) | Spatial navigation; arbitrary panel arrangement |
| **Mouse click** | Augmentation; not the primary path |

**Numeric jumps are fastest** when you have 5+ panels. Tab is fine for 2–3.

### Focus traps

Some panels should "trap" focus — Tab inside them cycles through internal widgets, not back to the global panel cycle. Modal dialogs and forms always trap focus. Use Esc to escape.

---

## Search and filter

Two distinct interactions:

### Search (forward through content)

Bound to `/`. Opens a search prompt; `Enter` jumps to first match; `n` / `N` cycles. Examples: vim's `/`, less's `/`, lazygit's `/`.

- Show match count: `(2/15)`.
- Highlight all matches; focus the current one with reverse video or accent.
- `Esc` cancels and returns to original position.

### Filter (narrow what's shown)

Bound to `/` (when search isn't needed) or another key. Filters the list to matching items. Examples: fzf's whole identity, k9s's `/`, Textual's `Input` widget on a list.

- Sub-100ms response — anything slower feels broken.
- Show count: `123/45678`.
- Highlight matched substring within results.
- `Esc` clears filter.

**Smart-case** is a kind courtesy: lowercase query is case-insensitive; mixed-case is case-sensitive. ripgrep, fzf, fd all default to this.

---

## Multi-select

Universal pattern: **Space toggles** the row's marked state. Marked rows show a `*` prefix or accent background.

Variants:
- **Visual mode** (`v`): yazi and vim — extend selection with motion keys.
- **Range select** (Shift+Click or Shift+arrow): from current to clicked.
- **Select all** (`Ctrl+A`): mark everything — with the caveat that `Ctrl+A` is tmux's common prefix and readline's start-of-line, so keep an alternative binding.
- **Invert** (`*` or another printable key): swap marked/unmarked. Avoid `Ctrl+I` — in the legacy encoding it's indistinguishable from Tab (only the Kitty keyboard protocol tells them apart), and Tab is your focus-cycle key.

After multi-selecting, an action key applies to all marked items: `d` deletes all marked, `y` yanks all, etc.

---

## Mouse support — the real trade-off

The fight between camps:

### Pro-mouse

- Textual treats mouse as first-class with `:hover`, click, scroll wheel.
- btop has full mouse including draggable boxes.
- lazygit selects on click.
- Modern users expect to be able to click things.

### Anti-mouse

- vim, helix, fzf purists.
- Mouse interferes with terminal text-selection (Shift bypasses in most emulators).
- Adds complexity without speed benefit for power users.

### The pragmatic compromise

**Mouse augments keyboard, never replaces required actions.** Every mouse-reachable target needs a keyboard equivalent.

Implement mouse for:
- Clicking a panel to focus it.
- Clicking a tab to switch.
- Scrolling lists / viewports.
- Clicking buttons in forms.

Don't require mouse for:
- Anything in the critical path.
- Power-user actions.
- Anything that should work over a serial console or restricted SSH.

**Document the Shift-bypass** for text selection. When mouse capture is on, regular click-drag selects via the app, not via the terminal. Users learn this pattern from one app and transfer it.

---

## Undo / redo

Hard for non-editor apps, but lazygit notably tracks every git action with `z` (undo) / `Ctrl+z` (redo) — even file operations and rebases. This is a *huge* user comfort feature for destructive tools.

**Two implementation strategies:**

1. **Action stack** — model every user action as a reversible operation. On undo, pop and reverse.
2. **State snapshots** — periodically snapshot full state; undo restores a snapshot. Cheaper to implement but coarser.

For destructive actions without undo, use modal confirmation. **Never silently destroy.**

---

## Confirmation patterns

Three levels of friction:

### Light: y/n prompt

```
Delete 3 files? [y/N]
```

Default to **No** — pressing Enter shouldn't delete.

### Medium: typed name

```
This will delete the production database.
Type the database name to confirm: prod-main
```

Used by Heroku for app deletion. Forces the user to *think* about what they're deleting.

### Heavy: dual confirmation

```
Step 1: Type "delete" to confirm
> delete

Step 2: Are you sure? [y/N]
```

For nuclear actions. Used rarely.

**Match friction to consequence.** Y/n for "stage all files" is fine. Typed name for "delete production." Don't make every confirmation typed-name — users learn to just type fast and lose the safety.

---

## Talking to the terminal emulator — OSC 8, 52, 9

Some interactions aren't between the user and your app — they're between your app and the *terminal emulator*: open a link, set the clipboard, pop a desktop notification. OSC escape sequences carry these requests in-band, down the same byte stream as your output. That's their superpower: they traverse SSH, containers, and nested shells, because the emulator on the user's *local* machine interprets them — no X11 forwarding, no remote clipboard daemon.

### OSC 8 — hyperlinks

`ESC ] 8 ; params ; URI ESC \` … link text … `ESC ] 8 ; ; ESC \`. The optional `id=` param stitches one logical link across wrapped lines or split regions so all its cells underline together on hover; simple filters shouldn't set ids, full-screen apps that manage the screen should.

**Support:** iTerm2, kitty, WezTerm, Ghostty, foot, Windows Terminal (1.4+), Alacritty (0.11+), tmux 3.4+. Degradation is graceful — a terminal that doesn't know OSC 8 ignores it and renders the visible text normally — but strip it when stdout isn't a TTY, or the raw bytes land in files and pipes.

**Libraries:** lipgloss has a `Hyperlink` style property (termenv underneath); Rich/Textual support links via the `link` style attribute. **Ratatui has no native support** — escape sequences inside `Text`/`Span` break its per-cell width accounting (open issues #563/#1227); workaround crates (`hyperrat`, `tui-link`) exist but work around the buffer model rather than fixing it.

**Over SSH, remember the link opens on the local machine.** A `file://` URI pointing at a remote path won't resolve. For "open this file," suspend and spawn `$EDITOR` on the remote side instead; save OSC 8 for `https://` URLs and the like.

### OSC 52 — write the system clipboard

`ESC ] 52 ; c ; <base64 payload> ESC \` asks the emulator to set the system clipboard — from anywhere, including over SSH. Practical limits: the common ceiling comes from xterm/hterm's 100,000-byte maximum sequence length, ≈74,994 bytes of decoded text; older kitty builds capped far lower. Keep payloads to tens of KB or chunk them.

**tmux:** `set-clipboard` controls forwarding — `on` lets inner apps set the outer clipboard; `external` (the default since 2.6) reserves that for tmux itself. Forwarding needs the outer terminal's `Ms` terminfo capability. tmux understands OSC 52 natively — it does **not** need `allow-passthrough`.

**Security:** writing is the safe half. Clipboard *reads* are how a malicious remote exfiltrates data, so most terminals disable or prompt on them (kitty prompts; WezTerm ignores queries; Alacritty disabled paste-back by default in 0.13). Windows Terminal even gates writes on window focus (since Feb 2026). Design for write-only.

**Libraries:** crossterm 0.29 added OSC 52 copy; Bubble Tea v2 ships `tea.SetClipboard`. Still provide a local fallback (`pbcopy` / `xclip` / `wl-copy`, or Rust's `arboard`) — OS clipboard APIs are more reliable when you're not over SSH, and some terminals disable OSC 52 entirely.

### OSC 9 / 777 — desktop notifications

`ESC ] 9 ; message ESC \` (OSC 9, iTerm2-originated) has the widest support: kitty, WezTerm, Ghostty, iTerm2, foot. OSC 777 (`ESC ] 777 ; notify ; title ; body ESC \`) adds a title where supported (WezTerm, Ghostty, foot); a reasonable strategy is 777 where you know it works, else 9. tmux swallows both unless wrapped in DCS passthrough with `allow-passthrough on` (tmux 3.3+).

**Etiquette:** notify only when long-running work finishes (or fails) while the user is likely elsewhere — build done, tests finished, deploy complete. Fire once, keep it short, prefer in-UI status when the app has focus. Never notify for routine events or things the user just did.

### The rest of the family, in one line each

- **OSC 11** — query the terminal's background color (`OSC 11 ; ? ST`); the standard light/dark detection trick, covered under Theming in `visual-patterns.md`.
- **Bracketed paste (mode 2004)** — the terminal wraps pastes in `ESC [200~ … ESC [201~` so apps can tell paste from typing; any prompt reading free text should enable it (frameworks generally do).

---

## The fzf pattern in detail

The "instant fuzzy filter" interaction has spread far beyond fzf itself: telescope.nvim, atuin, zoxide, helix's `Space+f`, Textual's command palette, k9s's `/`, lazygit's `/`.

The pattern:

1. **Open** with a key (often `/` or `Ctrl+P`).
2. **Type to filter** — shows results updating in real time.
3. **Arrow / hjkl** to navigate filtered results.
4. **Tab** to mark for multi-select (in `--multi` mode).
5. **Enter** to confirm; **Esc** to cancel.
6. **Optional preview pane** (right side) showing detail of hovered result.

Implementation rules:
- **Sub-100ms updates** as the user types.
- **Match count visible** — `123/45678`.
- **Highlight matched substring** within each result.
- **Smart-case** by default (lowercase = case-insensitive).
- **Sensible result ranking** — exact matches first, then prefix, then substring.

For Go: `sahilm/fuzzy` or `lithammer/fuzzysearch`. For Rust: `nucleo` (used by helix) or `skim`'s matcher. For Python: `rapidfuzz`. For TS/JS: `fuse.js` or `fzy.js`.

---

## The lazygit pattern — multi-pane with numeric tabs

Used by: lazygit, lazydocker (and inspired by mc / Norton Commander).

**Recipe:**
1. 5+ persistent panels in fixed positions.
2. `1`–`9` keys jump directly to numbered panels.
3. `Tab` cycles in order.
4. **Single letters trigger panel-specific actions** — `c` does something different in each panel.
5. **Footer hint bar updates per panel** — shows which actions `c` and friends do *right now*.

**The bet:** users tolerate context-sensitive single letters in exchange for dense bindings, *because the footer always shows what each key does in the current context.*

**The trade-off:** higher cognitive load — `c` does N different things. The footer hint bar is what makes it work.

---

## The k9s pattern — command-driven

Used by: k9s, helix (`:` ex-commands), weechat (`/` slash-commands), aerc.

**Recipe:**
1. Press `:` to enter command mode.
2. Type a resource type or command name (`pods`, `nodes`, `svc`, `ingress`).
3. Tab-completion narrows.
4. Enter runs.
5. Aliases for common commands (`po` = `pods`).

**Pros:** fast for power users, scales to many commands.

**Cons:** demands tab-completion or a discoverability layer (k9s shows aliases in `?`). Without it, users won't know what's possible.

**When to use:** when there are many resource types or actions, and users will repeat them often.

---

## The helix pattern — selection-first modal editing

Helix's bet against vim: select first, then act. `wd` selects-word-then-deletes (vs vim's `dw` "delete-word"). Multi-cursor is core. Tree-sitter integration. `Space` opens which-key.

**Why it matters for general TUI design:**
- **Selection-then-act** has visual feedback before the destructive action — users see what they're about to delete.
- **Multi-cursor** as primary scales beautifully for batch edits.
- **Which-key for leader keys** is a discoverability pattern any modal app should consider.

You probably won't build a modal editor, but the *visual-feedback-before-action* principle is widely applicable: highlight the rows you're about to delete, the field about to be cleared, the URL about to be visited.

---

## Common interaction pitfalls

1. **Reserved-key binding** (Ctrl+C, Ctrl+Z, Ctrl+S/Q). Don't.
2. **No focus indication.** Users tab around guessing which panel is active.
3. **Mode confusion** (modal apps with weak indicators). Use cursor shape + color.
4. **`q` doesn't quit.** Universal expectation.
5. **`Esc` doesn't back up.** Universal expectation.
6. **No `?` help.** Universal expectation.
7. **Filter that's slow** (>100ms updates).
8. **Destructive single-letter without confirmation or undo.** Either confirm or implement undo.
9. **Inconsistent meanings for the same key across panels** without a footer hint bar to explain.
10. **Mouse-only actions** with no keyboard equivalent.
11. **Tab order that skips around** (not following visual reading order).
12. **No multi-select where users need it** (file managers, lists of items to act on).

When reviewing a TUI's interaction design, walk this list. Most existing apps fail on 4–6 items.
