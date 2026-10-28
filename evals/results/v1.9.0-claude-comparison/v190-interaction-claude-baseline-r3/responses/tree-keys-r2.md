Here's a solid baseline, taken from the conventions most terminal users already know (file managers, nvim-tree/NERDTree, VS Code's explorer, Textual/Bubble Tea tree widgets).

## Core navigation

| Key | Behavior |
|---|---|
| `↑` / `k` | Move to previous visible node |
| `↓` / `j` | Move to next visible node |
| `→` / `l` | Collapsed node: expand it. Expanded node: move to its first child. Leaf: do nothing (or open it, if you want `l` to mean "go in") |
| `←` / `h` | Expanded node: collapse it. Collapsed node or leaf: jump to the parent. **This is the most important one to get right.** |
| `Enter` | Activate: open a leaf, toggle a branch |
| `Space` | Toggle expand/collapse, or toggle selection if you support multi-select (pick one meaning and stick to it) |
| `Home` / `g g` | First node |
| `End` / `G` | Last visible node |
| `PgUp` / `PgDn`, `Ctrl-u` / `Ctrl-d` | Page or half-page scroll, with the cursor moving too |

## Expand and collapse in bulk

- `*` or `E`: expand everything under the current node, recursively. Guard this on huge or lazy-loaded trees.
- `-` or `W`: collapse all, or collapse to the current node's siblings.
- `P` or `Backspace`: jump to the parent without collapsing anything.
- Optional: `zo` / `zc` / `zR` / `zM` (vim fold keys) for vim-heavy users.

## Search and filter

- `/`: incremental search. Jump to matches as the user types, and auto-expand ancestors to reveal hidden matches.
- `n` / `N`: next and previous match.
- Type-ahead (typing letters jumps to the next sibling starting with them) is nice when you don't have `/`.
- Filter mode, which hides non-matches but keeps their ancestors, is a separate, more powerful feature. Show clearly when a filter is active.
- `Esc`: clear the search or filter and return to normal mode.

## Selection (if needed)

- `Space` or `v` toggles the mark on a node. Show the mark visibly, e.g. `●` or a highlighted gutter.
- `Shift+↑/↓` extends a range selection.
- Decide what marking a parent means: does it select the whole subtree? Tri-state checkboxes (`[ ]` `[-]` `[x]`) make partial selection visible.

## Visual behavior

- **Expand indicators:** `▸` / `▾` (or `+` / `-` as an ASCII fallback). Leaves get blank space so labels stay aligned.
- **Indent guides:** `│ ├─ └─` help a lot with deep trees. Make them optional, since some people find them noisy.
- **Cursor:** a full-width highlighted row. It must stay visible when the terminal has no color (use reverse video).
- **Scrolling:** keep a few rows of context above and below the cursor (scrolloff ≈ 2–3), and never let the cursor leave the viewport.
- **Long labels:** truncate with `…` instead of wrapping. Wrapping breaks the one-row-per-node model.
- **Breadcrumb or status line:** show the current node's path, e.g. `src › components › Button.tsx`. Deep trees lose context without it.

## Behavior details that separate good trees from bad ones

1. **Remember expansion state** when a node is collapsed and reopened, so its expanded children stay expanded. Optionally persist it across sessions.
2. **Keep the cursor stable when data refreshes.** Track the selected node by ID, not by row index. If it gets deleted, fall back to its next sibling, then previous sibling, then parent.
3. **Load children lazily** for big or remote trees. Show `⋯ loading` under the node, don't block input, and show a clear inline error if loading fails.
4. **Don't let the cursor wrap** from bottom to top by default. Wrapping disorients people in long lists.
5. **Show empty branches differently** from unloaded ones, e.g. a dim `(empty)` child.
6. **Mouse support** (if enabled): click selects, click on the arrow or double-click toggles, wheel scrolls.
7. **Accessibility:** everything must work without color, and arrow keys must always work. Vim keys are additions, not replacements.
8. **Discoverability:** `?` opens a help overlay, or show a one-line key hint footer.

## Minimum viable set

If you only build part of this, build these: `↑↓`/`jk`, `←→`/`hl` with the parent-jump behavior above, `Enter`, `/` search, `g`/`G`, a visible cursor in monochrome, and cursor stability across refreshes. That covers about 90% of what users expect.

If you tell me which framework you're using (Textual, Bubble Tea, Ratatui, Ink, etc.), I can map these to its tree widget or sketch an implementation.
