A tree view should treat `→` and `←` as "go deeper" and "go back up," with each key doing the most useful thing for the node under the cursor. It also needs to remember which nodes are expanded by node ID so refreshes and filters don't lose that state.

## Core navigation keys

| Key | On a folder | On a leaf, or a node that's already collapsed |
|---|---|---|
| `→` / `l` | Expand it. If it's already open, move to its first child | Open or activate it |
| `←` / `h` | Collapse it | Move to the parent |
| `Enter` | Toggle it, or open it if the node has its own action | Open or activate it |
| `↑`/`↓`, `k`/`j` | Move one visible row | Same |

The second column is what makes the tree fast. Holding `→` walks down a branch, and holding `←` collapses back to the root. Users never have to aim at a small toggle.

Accept both arrow keys and `hjkl`. If the tree shares the screen with a text field, the letters must type normally while that field has focus.

## Keys shared with lists

| Key | Action |
|---|---|
| `g` / `G`, `Home` / `End` | Top / bottom |
| `PgUp` / `PgDn` | One page, keeping one row of overlap |
| `Ctrl+U` / `Ctrl+D` | Half a page |
| `/` | Filter (see the behaviors below) |
| `n` / `N` | Next / previous match |
| `Space` | Mark the node for multi-select. Action keys like `d` or `y` then apply to every marked node |
| `Esc` | Clear the filter or the marks. It never quits the app |
| `?` | Help |

Expand-all and collapse-all are optional extras. Use printable keys for them. Avoid `Ctrl+A`: tmux, GNU screen and readline already use it.

## Behaviors that matter more than the keys

1. **Store expansion and selection by node ID, not row number.** A refresh, sort, or filter should leave the tree looking the same. If the selected node disappears, select its nearest surviving sibling, not the first row.
2. **Filtering keeps the path to each match.** When `/` is active, keep every ancestor of every match visible and expanded so each result has context. Show a count like `12/4,310` and highlight the matched text. `Esc` restores the expansion state from before the filter.
3. **Load children only when a node is expanded.** Show a spinner on that row only, not a global "Loading…" that blocks the whole tree. If loading fails, show the error on that node's row and let the user retry there.
4. **Keep the cursor 3 rows from the viewport edge** while it moves (1 row in short panes). Show your position as `42/1,203` in the panel title or footer.
5. **Indent 2 cells per level and draw connectors**: `├─` and `└─`, with `|-` and `` `- `` as the ASCII fallback. Mark expanded and collapsed nodes with shape (`▾`/`▸`, or `v`/`>` in ASCII), never color alone.
6. **Render only the visible rows.** Store the tree as nested data but build a flat list of visible rows for the viewport. Trees grow to thousands of nodes quickly.

```
▾ src/                      42/1,203
  ├─ ▸ components/
  ├─ ▾ lib/
  │   ├─ parse.ts
  │   └─ ⠋ generated/          ← per-node spinner
  └─ index.ts
```

## At narrow widths

Deep nesting uses up columns. In a 60-column split, cut labels short with `…` rather than wrapping them, and show the full name in a detail line or the status bar. Past roughly 6–8 levels, consider drill-down instead: `Enter` makes the node the new root and a breadcrumb shows the path. If the tree sits next to a preview pane, switch to a single pane below about 80 columns and open the preview on demand. File managers like yazi and ranger do this with three side-by-side columns (parent, current, preview).

Tell me your framework (Bubble Tea, Ratatui, Textual, Ink…) and I can say which of these its tree widget already handles and what you'd need to add yourself.
