# Interaction patterns — keybindings, focus, navigation, modal vs modeless

A deep dive into how users interact with TUIs — keybinding philosophy, focus management, navigation patterns, mouse support, and discoverability. The top-level `SKILL.md` covers the principles; this file goes deeper into the *why* and the trade-offs.

**Contents:**
- [Keybinding philosophies and modal vs modeless](#keybinding-philosophies-and-modal-vs-modeless)
- [Cross-app keybinding conventions](#cross-app-keybinding-conventions)
- [Reserved keys — preserve what users expect](#reserved-keys--preserve-what-users-expect) · [Esc, q, and Ctrl+C — the quit ladder](#esc-q-and-ctrlc--the-quit-ladder) · [Keys the environment steals](#keys-the-environment-steals)
- [Discoverability — the four-layer pattern](#discoverability--the-four-layer-pattern)
- [Focus management](#focus-management)
- [Search and filter](#search-and-filter)
- [Scrolling and position](#scrolling-and-position) · [Live data — keeping the selection steady](#live-data--keeping-the-selection-steady) · [Logs and streams — follow mode](#logs-and-streams--follow-mode)
- [Multi-select](#multi-select) · [Tree views](#tree-views)
- [Mouse support — the real trade-off](#mouse-support--the-real-trade-off)
- [Undo / redo](#undo--redo) · [Confirmation patterns](#confirmation-patterns)
- [Text input — fields, history, completion](#text-input--fields-history-completion) · [Forms and settings screens](#forms-and-settings-screens)
- Named patterns: [fzf](#the-fzf-pattern-in-detail) · [lazygit](#the-lazygit-pattern--multi-pane-with-numeric-tabs) · [k9s](#the-k9s-pattern--command-driven) · [helix](#the-helix-pattern--selection-first-modal-editing)
- [Common interaction pitfalls](#common-interaction-pitfalls)

Terminal modes, escape sequences (paste, keyboard and mouse protocols, OSC 8/52/9), and multiplexer, SSH, and Windows behavior live in `terminal-protocols.md`.

---

## Keybinding philosophies and modal vs modeless

Most apps blend four schools:

| School | Identity | Examples | Costs |
|---|---|---|---|
| **Modal (vim-style)** | Modes (NORMAL, INSERT, VISUAL, COMMAND); single-letter motions and operators with counts (`5dw`), leader keys for namespaces. Dense and composable, no Ctrl/Alt needed | vim, helix, kakoune, k9s (ex-mode), aerc | Steep learning curve; mode confusion when the indicator is weak; modal text input fights conventional editing (Ctrl+A, Ctrl+E) |
| **Chord (Emacs-style)** | Modifier-prefixed bindings (`C-x C-s`, `M-x`), no modes, nested key tables; discoverable with which-key | emacs, readline shells, weechat | Modifier strain; collides with terminal-reserved keys; slower than modal for repetitive editing |
| **Modeless (arrow / GUI-like)** | Arrows, Enter, Tab, Esc, single-letter shortcuts; state changes via widget focus; mouse-friendly; zero learning curve | btop, htop, fzf, gum, Posting, Harlequin, most Textual apps | Fewer keys means fewer commands; Ctrl/Alt for less-common actions; screen space spent on focus indicators |
| **Hybrid** | On navigational surfaces, arrows and compatible `hjkl` aliases together. Vim shortcuts are power-user paths, never requirements, and printable aliases yield while a text field owns input | lazygit, k9s, yazi, gh dash | Slightly more code; risk of inconsistent key meanings |

**Decision rule.** Default to hybrid for a new navigational, full-screen TUI. A bounded prompt or form can keep a smaller conventional keymap. Go modal only for editor-like tools where keystrokes are the primary interaction and users are likely vim-familiar, never for a general-purpose tool aimed at non-vim users. Choose chords only when inheriting a convention; rarely from scratch.

- **Modal needs** a persistent mode indicator (status-bar color or label), a distinct cursor shape per mode (block in NORMAL, bar in INSERT, underline in REPLACE) reset on exit (`terminal-protocols.md` → *Modes and sequences*, cursor shape), and a way to learn the modes.
- **Modeless needs** clear focus indication (see *Focus indicators*) and modifier bindings for less-common actions.
- **Contextual bindings** let the focused panel decide what a key means: lazygit's `space` stages in Files, checks out in Branches, applies in Stash, and k9s adds panel-specific actions to the global ones. This is context-sensitive modeless; it works when panel-specific actions are rich and a footer hint bar shows what each key does right now.

---

## Cross-app keybinding conventions

These have crystallized across the ecosystem. Use them unless you have a strong reason not to:

| Key | Action |
|---|---|
| `q` | back out of a nested view; quit at the root (see *Esc, q, and Ctrl+C*) |
| `?` | help |
| `/` | search / filter |
| `n` / `N` | next / prev match |
| `Esc` | one step down the quit ladder: cancel, close overlay, clear filter, back (see *Esc, q, and Ctrl+C*) |
| `Enter` / `Return` | confirm / drill in |
| `Space` | toggle / mark for multi-select (`Tab` in type-to-filter pickers; see *Multi-select*) |
| `:` | command mode |
| `gg` / `G`, `Home` / `End` | top / bottom |
| `PgUp` / `PgDn`, `Ctrl+U` / `Ctrl+D` | page / half page (see *Scrolling and position*) |
| `Tab` / `Shift+Tab` | switch focus |
| `r` | refresh |
| `1`–`9` | jump to panel / numbered tab |
| `hjkl` *and* arrows | move in navigational views when text entry does not conflict |
| `Ctrl+P` | command palette, when the app includes one (keep an alternative; see *Layer 4*) |
| `y` | yank / copy |
| `p` | paste / push |
| `d` | delete (often confirms first) |
| `e` | edit |
| `o` | open |

**Pick a paradigm and stay consistent.** Don't mix `Ctrl+S` and `:w` for save unless both clearly map to "write file."

---

## Reserved keys — preserve what users expect

In cooked (line) mode these keys belong to the terminal driver and shell. In raw mode, which every full-screen framework enables (`cfmakeraw` also clears `IXON`), they arrive as ordinary keypresses: no SIGINT, SIGTSTP, or XOFF is generated unless your app produces that behavior itself. Flow-control freezes (and the `stty -ixon` workaround) only matter for cooked-mode programs.

| Key | Expected behavior |
|---|---|
| **Ctrl+C** | Interrupt — cancel the current operation or quit cleanly |
| **Ctrl+Z** | Suspend — restore the terminal, stop, and redraw on `fg` |
| **Ctrl+\\** | Abort — SIGQUIT (core dump) in cooked mode |
| **Ctrl+S** / **Ctrl+Q** | XON/XOFF flow control (cooked mode only; see above) |

A full-screen app *may* handle these keys, and real ones do: helix binds `Ctrl-c` to toggle comments and `Ctrl-s` to `save_selection`; nano and micro save on `Ctrl+S`. What you owe users is the expected behavior, not a hands-off policy: keep `Ctrl+C` as cancel/quit unless there's a strong reason not to (and then offer an obvious exit), and implement `Ctrl+Z` suspend through the framework's support so the terminal is restored.

Ctrl+H is sometimes Backspace, sometimes a free key — it depends on terminal config. Test before binding.

---

## Esc, q, and Ctrl+C — the quit ladder

`Esc` has five jobs in most apps and no order between them. Make it one rule: **each press takes the innermost step that applies, once, and quitting comes last.**

| Step | Applies when | Esc does |
|---|---|---|
| 1. Cancel | A request, load, or long action is running | Cancels it and keeps the old data |
| 2. Close | A modal, menu, palette, help screen, or completion popup is open | Closes the top one only |
| 3. Clear | A filter, search, or multi-selection is active | Clears it, and a cancelled search returns to the prior position |
| 4. Go back | A drill-down, detail view, or focus trap is open | Backs up one level |
| 5. Root | Nothing above applies | Nothing: `Esc` never quits |

- **`q`** goes back one level in a nested view and quits only at the root. While a text field owns input it is a letter. In a single-view app it quits.
- **`Ctrl+C`** cancels a running operation first. With nothing running it quits from anywhere, without walking the ladder. When quitting would lose something, the first press says so on the status line (`Press Ctrl+C again to quit`) and a second press within about two seconds quits.
- **Confirm a quit only when it loses something**: unsaved edits, or running work that cannot resume (`Quit? 2 jobs are still running [y/N]`, default No, per *Confirmation patterns*). An idle quit never asks.
- Every quit path runs the same teardown (`SKILL.md` → *Terminal lifecycle*), including the second `Ctrl+C` and a confirmed `q`.

A lone `Esc` is ambiguous with the start of an Alt sequence, so don't make it latency-critical (see *Keys the environment steals*).

---

## Keys the environment steals

Multiplexers, shells, and the legacy key encoding take or merge keys before your app sees them. Design the keymap around that, and read `terminal-protocols.md` → *Terminal environments* before shipping a Ctrl or Alt binding.

| Key | Who takes it | Design response |
|---|---|---|
| **Ctrl+B** | tmux prefix | Never the only path to an action |
| **Ctrl+A** | GNU screen prefix; readline line-start | Same; don't bind it as the leader |
| **Ctrl+G/P/T/N/H/S/O/Q/B**, many Alt keys | Zellij's default mode (the Unlock-First preset frees the Ctrl keys, not Alt) | Keep a non-Ctrl, non-Alt path to every action |
| **Ctrl+P** | readline previous-history; Zellij | Offer `:` or a leader key too (see Layer 4) |
| **Ctrl+I / H / M / [** | Legacy encoding: the same byte as Tab, (often) Backspace, Enter, Esc | Don't bind them separately from Tab, Backspace, Enter, Esc |
| **Shift+Enter, Ctrl+Enter, Ctrl+Tab** | Legacy encoding can't send them | Accelerators only: enable the kitty keyboard protocol where reported, and keep a legacy binding for every action |
| **Lone Esc** | tmux waits `escape-time` (500 ms before 3.5, 10 ms since) to tell Esc from an Alt sequence | Don't make Esc latency-critical, and test inside tmux |

---

## Discoverability — the four-layer pattern

Every action a user can take should be discoverable through *at least one* of these layers, in order of immediacy:

### Layer 1: Always-visible footer hints

For a full-screen app, keep the 3–5 most-useful shortcuts visible at the bottom and update them by context. For a complex app this is usually the strongest discoverability tool, since most users read what is visible rather than the docs. A one-step inline prompt can show its controls beside the prompt instead of reserving a footer row.

Examples: htop's F1–F10 strip, lazygit's per-pane hints (`space stage  c commit  P push  p pull  ?`), helix's status line.

Define keys *once*, derive the footer. **Bubble Tea**'s `bubbles/help` reads `key.KeyMap` and **Textual**'s `Footer` renders `BINDINGS`; **Ratatui** and **Ink** don't generate one, so build a helper that reads your keybinding map.

### Layer 2: `?` help screen

Pressing `?` opens a modal or full-screen help with **all** keybindings, grouped by mode, panel, or category (`key  action  context`). Every full-screen app with more than a handful of actions should provide this or an equivalent discoverable help view. A tiny picker whose complete keymap is already visible does not need a separate modal. lazygit's `?` shows a categorized list with sections per panel.

### Layer 3: Leader-key / which-key

After pressing a leader (Space, `,`, `\`), show a popup with the available follow-up keys. The user reads and picks, types the key to dismiss the popup and trigger the action, or presses Esc to cancel. helix's `Space-` menu is the gold standard (`f` file picker, `b` buffer picker, `s` symbols, `a` LSP actions); `which-key.nvim` is near-universal in neovim. Add one when your keymap exceeds ~20 distinct actions; below that, `?` help is enough.

### Layer 4: Command palette

`Ctrl+P` (or similar) opens a fuzzy-matched action list. The user types to filter. Keep an alternative binding: Zellij's default mode captures `Ctrl+P` and readline uses it for previous history. A route that needs no Ctrl chord, such as `:` or a leader key, avoids both collisions.

Add a palette once the app has more than about 20 actions, or when its actions span multiple contexts or benefit from search; a smaller app can stop at footer hints plus `?`. **Once a palette exists, every action that has a keybinding should also be a palette command.** The keybinding is the shortcut; the palette is the long-form name + searchable description. Show the keybinding next to each command name, so the palette doubles as keybinding documentation.

Examples: Textual's built-in palette (`Ctrl+P` by default since v0.77; it originally shipped on `Ctrl+\`, which collides with SIGQUIT), VS Code's Ctrl+Shift+P (the conceptual ancestor), and the `:` of helix and k9s (resource-typing, but the same "type to filter actions" model).

---

## Focus management

In a multi-panel TUI, **which panel has focus** determines:
- Which keystrokes the panel responds to.
- Which footer hints show.
- The visual highlight (see *Focus indicators*).

### Focus indicators (in order of strength)

Under `NO_COLOR` or a monochrome palette every color cue vanishes, so focus must be carried by a cue that does not depend on color (`SKILL.md` → *Meaning and access*). Rank the non-color cues first; color only reinforces:

1. **Border weight** — thin → thick (`┏━┓` for the focused panel, `┌─┐` for the rest). Survives monochrome.
2. **Selection visible** — only the focused panel shows reverse-video selection; unfocused panels show muted selection.
3. **Title marker or weight** — bold title, optionally with a marker such as `▸ Files`.
4. **Border color change** — the focused border takes the accent color. Strong where color exists, but never the only cue.
5. **Background tint** — subtle but be careful (background-leak issues with borders).

Pick one non-color cue plus color; the budget is in `visual-patterns.md` → *The clutter audit*.

### Focus navigation

| Method | Best for |
|---|---|
| **Tab / Shift+Tab** cycle | Linear panel order; small number of panels |
| **Numeric keys** (`1`–`9`) | Direct jumps; many panels or tabs (lazygit `1`–`5` panels, yazi `1`–`9` tabs) |
| **Directional** (`Ctrl+w h/j/k/l` like vim) | Spatial navigation; arbitrary panel arrangement |
| **Mouse click** | Augmentation; not the primary path |

**Numeric jumps are fastest** when you have 5+ panels. Tab is fine for 2–3.

### Focus traps

Some panels should "trap" focus — Tab inside them cycles through internal widgets, not back to the global panel cycle. Modal dialogs and forms always trap focus. Use Esc to escape.

---

## Search and filter

Two distinct interactions, usually on the same key: `/` filters lists and searches documents and logs, so the focused view decides which one it does.

### Search (forward through content)

Bound to `/` in documents and logs. Opens a search prompt; `Enter` jumps to first match; `n` / `N` cycles. Examples: vim's `/`, less's `/`, lazygit's `/`.

- Show match count: `(2/15)`.
- Highlight all matches; focus the current one with reverse video or accent.
- `Esc` cancels and returns to original position.

### Filter (narrow what's shown)

Bound to `/` in lists. Filters the list to matching items. Examples: fzf's whole identity, k9s's `/`, Textual's `Input` widget on a list.

- Sub-100ms response — anything slower feels broken.
- Show count: `123/45678`.
- Highlight matched substring within results.
- `Esc` clears filter.

**Smart-case** is a kind courtesy: lowercase query is case-insensitive; mixed-case is case-sensitive. fzf and fd default to this; ripgrep offers it as `-S`/`--smart-case`.

---

## Scrolling and position

| Keys | Moves |
|---|---|
| `↑`/`↓`, `k`/`j` | One row |
| `PgUp` / `PgDn` | One page, minus one row of overlap |
| `Ctrl+U` / `Ctrl+D` | Half a page |
| `Home` / `End`, `g` / `G` | Top / bottom |
| Mouse wheel | The viewport under the pointer, not the selection |

Keep the cursor at least 3 rows from the viewport edge while it moves (1 row in viewports under 12 rows tall), so the next rows are visible before the user reaches them. Show where the user is: `42/1,203` right-aligned in the panel title or footer for lists, a percentage for documents. A scrollbar is optional decoration; the count carries the meaning, survives screen readers, and costs no width.

---

## Live data — keeping the selection steady

Lists that refresh (processes, pods, builds) move under the user's cursor unless you prevent it.

- **Track the selection by a stable ID** (pod UID, file path, row key), never by row index, and re-resolve it after every refresh, sort, and filter.
- **If the selected ID disappears,** select its nearest surviving neighbor (the next row, else the previous), not the first row.
- **Don't scroll under the cursor.** When rows insert or vanish above the selection, keep the selected row at the same screen position; move the viewport only when the selection would leave it.
- **Don't re-sort on refresh** unless the user changed the sort. A list sorted by a volatile key (CPU%) reorders constantly by design.
- **Offer a freeze key** shown in the footer (htop's `Z` pauses updates). While frozen, stop reorders and appends, mark the header `PAUSED`, show the count of pending changes, and apply them on resume.

---

## Logs and streams — follow mode

A viewer for output that keeps arriving (logs, build output, chat transcripts) has two states, and the user must always know which one it is in.

- **Following:** pinned to the bottom; new lines scroll in. This is the default on open.
- **Paused:** any upward movement (`k`, `PgUp`, wheel up, `g`) stops following and holds the viewport still. Show the backlog in the corner: `▾ 37 new`. `G` (jump to the end) or `F` (toggle follow, as in `less`) re-pins.
- **Wrap toggle** (`w`): wrapped by default for prose, unwrapped (truncate with `…` and scroll sideways) for columnar or JSON logs.
- **Ring buffer.** Cap retained lines (10,000–100,000 is typical) and say when the oldest were dropped (`oldest 52,310 lines dropped`); offer to write the full stream to a file if users need it.
- A filter keeps following: new lines that match appear, and the count updates.

---

## Multi-select

Universal pattern: **Space toggles** the row's marked state when no text field owns input. In a type-to-filter picker (fzf `--multi`), Space is a query character, so **Tab** marks the row instead (fzf marks and moves down; Shift+Tab marks and moves up) and no longer cycles focus. Marked rows show a `*` prefix, with an accent background as reinforcement.

Variants:
- **Visual mode** (`v`): yazi and vim — extend selection with motion keys.
- **Range select** (Shift+Click or Shift+arrow): from current to clicked.
- **Select all** (`Ctrl+A`): mark everything — with the caveat that `Ctrl+A` is GNU screen's prefix (and a common tmux rebinding) and readline's start-of-line, so keep an alternative binding.
- **Invert** (`*` or another printable key): swap marked/unmarked. Avoid `Ctrl+I` — in the legacy encoding it's indistinguishable from Tab (only the Kitty keyboard protocol tells them apart), and Tab is your focus-cycle key.

After multi-selecting, an action key applies to all marked items: `d` deletes all marked, `y` yanks all, etc.

---

## Tree views

| Key | On a folder | On a leaf or collapsed child |
|---|---|---|
| `l` / `→` | Expand; if already open, move to its first child | Open or activate |
| `h` / `←` | Collapse | Move to the parent |
| `Enter` | Toggle, or open when the node has an action | Open or activate |

- Indent 2 cells per level, with connectors (`├─ └─`, ASCII fallback `|-` and `` `- ``).
- Load children lazily and show a per-node spinner on the row being expanded, not a global one.
- **Keep expansion state by node ID** across refreshes and filters. When a filter is active, keep the ancestors of every match visible and expanded.

---

## Mouse support — the real trade-off

Textual treats the mouse as first-class (`:hover`, click, wheel), btop makes every highlighted key clickable, and lazygit selects on click, range-selects by dragging, and reorders commits by dragging (v0.64+). Keyboard-first users resist it, and capture has a cost: it takes over click-and-drag text selection, so users must hold a bypass modifier (Shift in most terminals, Option in iTerm2, Fn in Terminal.app). helix and fzf turn the mouse on by default but never require it.

**Default for full-screen apps with click targets:** enable modes 1000 + 1002 + 1006 (press and release, drags, SGR coordinates), and 1003 only for hover effects, since it reports every pointer move (`terminal-protocols.md` → *Modes and sequences*). Provide an off switch (`--no-mouse` or a config key). Inline tools leave the mouse off, so selection and scrollback keep working.

**Mouse augments keyboard, never replaces required actions.** Every mouse-reachable target needs a keyboard equivalent. Implement mouse for focusing a panel, switching tabs, scrolling lists and viewports, and clicking form buttons. Don't require it for the critical path, power-user actions, or anything that should work over a serial console or restricted SSH.

**Document the selection bypass** for your users' terminals, since the modifier isn't always Shift, and offer a way to turn mouse capture off. Inside tmux 3.8+, the bypass is needed even for apps that never enable the mouse (`terminal-protocols.md` → *Terminal environments*).

---

## Undo / redo

Hard for non-editor apps, but lazygit offers `z` (undo) / `Z` (redo) for git actions recorded in the reflog: commits, checkouts, resets, even a botched rebase. It states its limits: working-tree and stash changes, pushes, and branch creation can't be undone, and undo is unavailable mid-rebase. Even bounded, this is a large comfort for destructive tools.

Implement it as an **action stack** (each action a reversible operation; pop and reverse) or **state snapshots** (cheaper, coarser). For destructive actions without undo, use confirmation. **Never silently destroy.**

---

## Confirmation patterns

Match friction to consequence, in three levels:

- **Light, y/n prompt:** `Delete 3 files? [y/N]`. Default to **No**, so pressing Enter doesn't delete.
- **Medium, typed name:** `Type the database name to confirm: prod-main` (Heroku's app deletion). Forces the user to think about what they're deleting.
- **Heavy, dual confirmation:** type `delete`, then answer `Are you sure? [y/N]`. For nuclear actions; used rarely.

Y/n suits "stage all files"; a typed name suits "delete production." Don't make every confirmation typed-name: users learn to type fast and lose the safety.

---

## Text input — fields, history, completion

Free-text fields matter most in chat and agent TUIs, where the field is the product.

- **Editing keys.** Arrows, `Home`/`End`, `Backspace`/`Delete`, and `Ctrl+W` (delete word), `Ctrl+U` (delete to line start), `Ctrl+K` (delete to line end), and `Ctrl+A`/`Ctrl+E` as aliases, never the only route: `Ctrl+A` is GNU screen's prefix (see *Keys the environment steals*).
- **History.** `↑`/`↓` recall previous entries when the cursor is on the first or last line of the field (any press in a single-line field). Keep history across sessions and skip consecutive duplicates.
- **Completion and ghost text.** Show the suggestion dimmed after the cursor; `→` or `End` accepts it, as fish does. `Tab` completes when a completion exists (the first press lists candidates when several match); otherwise it moves focus. A field that completes owns `Tab`, so move focus with `Esc` then `Tab`, or with a dedicated key.
- **Multi-line submit.** In chat-style fields `Enter` sends and a modifier inserts a newline. `Shift+Enter` is distinct from `Enter` only with the kitty keyboard protocol, so fall back to `Alt+Enter` or `Ctrl+J` (a line feed, distinct from `Enter`'s carriage return in the legacy encoding), and a trailing `\` then `Enter` as a third route. State the newline key in the placeholder or footer (`Enter send ⋅ Alt+Enter newline`). In editor-like fields invert it: `Enter` inserts a newline and `Ctrl+Enter` or `Ctrl+S` sends. Bracketed paste inserts pasted newlines and never submits (`terminal-protocols.md` → *Modes and sequences*).
- **Validation timing** is under *Forms and settings screens* below.

---

## Forms and settings screens

### Validation timing — avoid premature errors

Default to validation on **blur** or **submit** so an incomplete value is not treated as an error while the user is still typing. huh's `Input` validates when a field loses focus and again on Next/Submit — there's no per-keystroke validation path in its implementation. Clack and Inquirer validate only on Enter (there's no blur concept in a single-prompt-at-a-time flow). After an error has been shown, live revalidation can help it disappear as soon as the value becomes valid; expensive or remote checks should be debounced or reserved for submit.

Textual's `Input.validate_on` accepts `"blur"`, `"changed"`, and `"submitted"`, and **defaults to all three**. Narrow it to `validate_on=["blur"]` or `["submitted"]` when errors should wait; keep `"changed"` only when immediate feedback is useful and non-disruptive.

### Required-field marking — there is no framework convention

None of huh, Textual, or Clack/Inquirer ship a built-in "required field" visual marker (no asterisk-for-required the way GUI toolkits do). **Don't assume one exists — this is an easy claim to get wrong by GUI pattern-matching.** In particular, huh's `" *"` suffix is its **error indicator**, shown after a validation failure, not a required-field marker; there's no `Required()` API. If a design needs required fields marked, do it manually with label text such as `(required)` or an explained `*`; color may reinforce the marker but must not carry the meaning alone.

### Dynamic/conditional fields

Show or hide dependent fields as earlier answers change, and recompute choices from those answers. Check what your framework ships before designing around it: Huh hides whole groups, not single fields (`ecosystem-go.md` → *Huh*), and Textual hides a dependent widget from a reactive watcher (`ecosystem-python.md` → *Reactive state*).

### Settings-screen behavior — be honest about what's settled

There's no single widely adopted TUI convention for settings persistence. Choose from the behavior of the underlying operation rather than presenting one pattern as universal:

- **Live-apply** (htop's F2 setup screen): changes take effect immediately as you make them; persistence to disk happens implicitly, not via an explicit Save action. No dirty-state indicator, no discard.
- **Explicit Apply / Save / Cancel**: appropriate when changes must be validated together, committed atomically, trigger an expensive reload, or update a remote system. Show dirty state, make `Esc` behavior explicit, and confirm before discarding meaningful edits.
- **Defer to `$EDITOR`** (lazygit): no in-app settings form at all — press `e` in the Status panel to open the raw config file in the user's editor. Since v0.44, lazygit reloads the changed file when its terminal regains focus; only a few settings (refresh and fetch intervals, update checks) still need a restart, and lazygit says which. If you take this route, reload on focus or file change rather than demanding a restart.

There is no settled convention for Esc-to-discard on a dirty form. Design and document it explicitly, and match confirmation friction to the cost of losing the edits.

---

## The fzf pattern in detail

The instant-filter interaction has spread far beyond fzf: telescope.nvim, atuin, zoxide, helix's `Space+f`, and Textual's command palette match fuzzily; k9s's `/` (regex) and lazygit's `/` (substring by default) keep the instant filter with a stricter matcher.

1. **Open** with a key (often `/` or `Ctrl+P`).
2. **Type to filter** — shows results updating in real time.
3. **Arrow / `Ctrl+J` / `Ctrl+K`** to navigate while the query owns printable input. Reserve bare `hjkl` for an explicit navigation mode or a view with no active text field.
4. **Tab** to mark for multi-select (in `--multi` mode; why Tab and not Space: *Multi-select*).
5. **Enter** to confirm; **Esc** to cancel.
6. **Optional preview pane** (right side) showing detail of hovered result.

Implementation rules: everything in *Search and filter* → *Filter* (sub-100ms updates, match count, highlighting, smart case), plus **sensible result ranking** — exact matches first, then prefix, then substring.

For Go: `sahilm/fuzzy` or `lithammer/fuzzysearch`. For Rust: `nucleo` (used by helix) or `skim`'s matcher. For Python: `rapidfuzz`. For TS/JS: `fuse.js` or `fzy.js`.

**Case study:** `references/exemplar-apps.md` → *fzf*.

---

## The lazygit pattern — multi-pane with numeric tabs

Used by lazygit and lazydocker (after mc / Norton Commander): 5+ persistent panels in fixed positions, `1`–`9` jump to numbered panels, `Tab` cycles, and single letters trigger panel-specific actions (`c` does something different in each panel). The bet is that users tolerate context-sensitive letters for dense bindings *because the footer hint bar always shows what each key does right now*; without that bar the cognitive load is too high. Case study: `references/exemplar-apps.md` → *lazygit*.

---

## The k9s pattern — command-driven

Used by k9s, helix (`:` ex-commands), weechat (`/` commands), and aerc: press `:`, type a resource or command name (`pods`, `svc`), Tab-completion narrows, Enter runs, and aliases shorten common ones (`po` = `pods`). It is fast for power users and scales to many commands, but demands completion or a discoverability layer: k9s suggests completions as you type and lists every alias in its own view (`Ctrl-A`). Use it when there are many resource types or actions that users repeat often. Case study: `references/exemplar-apps.md` → *k9s*.

---

## The helix pattern — selection-first modal editing

Helix selects first, then acts (`wd` selects the word and deletes it, vs vim's `dw`), with multi-cursor as the core and `Space` opening which-key. The transferable principle is *visual feedback before the action*: highlight the rows you're about to delete, the field about to be cleared, the URL about to be visited. Which-key for leader keys suits any modal app. Case study: `references/exemplar-apps.md` → *helix*.

---

## Common interaction pitfalls

1. **Broken reserved-key expectations** — Ctrl+C that neither cancels nor quits, Ctrl+Z that doesn't suspend cleanly.
2. **No focus indication.** Users tab around guessing which panel is active.
3. **Mode confusion** (modal apps with weak indicators). Use cursor shape + color.
4. **`q` doesn't quit in a modeless full-screen app** (outside text entry), without offering another visible conventional exit.
5. **`Esc` doesn't back up or dismiss** where the UI establishes a navigation stack or modal.
6. **No discoverable key help** in an action-rich app; `?` is conventional, but an equivalent visible route is fine.
7. **Filter that's slow** (>100ms updates).
8. **Destructive single-letter without confirmation or undo.** Either confirm or implement undo.
9. **Inconsistent meanings for the same key across panels** without a footer hint bar to explain.
10. **Mouse-only actions** with no keyboard equivalent.
11. **Tab order that skips around** (not following visual reading order).
12. **No multi-select where users need it** (file managers, lists of items to act on).
13. **Selection jumps on refresh**, or a viewport that scrolls under the cursor (*Live data*).
14. **A log viewer that keeps scrolling while the user reads** (*Logs and streams*), or no way to tell it is paused.
15. **`Esc` that quits, or a `q` that quits from a nested view with unsaved work** (*Esc, q, and Ctrl+C*).

When reviewing a TUI's interaction design, walk this list.
