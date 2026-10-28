Here's a solid baseline that matches what users already know from file managers, ranger/lf, VS Code's explorer, and the WAI-ARIA tree pattern.

## Core navigation

| Key | Behavior |
|---|---|
| `↓` / `j` | Next visible node. Skip children of collapsed nodes. |
| `↑` / `k` | Previous visible node. |
| `→` / `l` | If the node is collapsed, expand it. If it's already expanded, move to its first child. On a leaf, do nothing. |
| `←` / `h` | If the node is expanded, collapse it. If it's collapsed or a leaf, jump to its parent. **This matters most.** It lets users climb out of deep trees quickly. |
| `Home` / `g` | First node |
| `End` / `G` | Last visible node |
| `PgUp` / `PgDn` (`Ctrl-u` / `Ctrl-d`) | Move one viewport (or half a viewport) at a time |
| `Enter` | Activate: open or select the node. On a branch, toggle it if there's no separate "open" action. |
| `Space` | Toggle expand/collapse, or toggle selection if you support multi-select. Pick one meaning and use it consistently. |

## Bulk expand/collapse

| Key | Behavior |
|---|---|
| `*` | Expand all siblings of the current node (from the ARIA convention), or recursively expand the current subtree |
| `-` / `=` (or `zc` / `zo`, `zM` / `zR` for vim users) | Collapse all / expand all |
| `Shift-→` / `Shift-←` | Optional: recursive expand/collapse of the current node |

Be careful with "expand all" on large or lazy-loaded trees. Cap the depth or ask for confirmation.

## Search and jump

- **Typeahead:** typing printable characters jumps to the next visible node whose label starts with that prefix. Reset the buffer after about 500 ms of no input. This conflicts with single-letter shortcuts, so choose one approach.
- **`/` filter or search:** keep the ancestors of matches visible so the context stays intact. Highlight the matched text. Use `n`/`N` for next/previous match and `Esc` to clear.
- **`p` or `P`:** jump to the parent without collapsing anything. This is useful when `←` collapses.

## Behaviors that are easy to get wrong

1. **Preserve the cursor through collapse.** When an ancestor of the cursor collapses, move the cursor to that ancestor. Don't reset to the top.
2. **Remember expansion state** when the tree refreshes or the data reloads. Key nodes by a stable ID, not by index.
3. **Keep the cursor visible.** Scroll with a margin (scrolloff of about 2–3 lines) so the user can see what's coming.
4. **Lazy loading:** show a `⋯ loading` child while it loads, keep the UI responsive, and show an error node if the load fails rather than failing silently.
5. **Empty branches vs. leaves:** render them differently. For example, a branch with no children shows `▸` dimmed or `∅`, and a leaf shows no arrow.
6. **Don't wrap at the ends** by default. Wrapping disorients people in long trees.
7. **Mouse, if supported:** click selects, click on the arrow toggles, double-click activates, and the scroll wheel scrolls the viewport without moving the cursor.

## Visual conventions

```
▾ src/
│ ├─ ▸ components/
│ ├─ ▾ utils/
│ │  ├─   format.ts
│ │  └─   parse.ts      ← cursor row: reverse video, full width
│ └─   index.ts
▸ tests/
```

- Use `▸`/`▾` (or `+`/`-` as an ASCII fallback) for collapsed and expanded nodes.
- Guide lines (`│ ├─ └─`) help a lot in deep trees. Make them toggleable for narrow terminals.
- Show the cursor and the selection differently if you have both. For example, the cursor is reverse video and selected nodes get a `●` marker or a color.
- Truncate long labels with `…` rather than wrapping. Optionally scroll horizontally when depth makes the indent too wide.
- Optional: show child counts on collapsed nodes (`▸ components/ (12)`).

## Multi-select (if needed)

- `Space` toggles the current node, `Shift-↑`/`Shift-↓` extends a range, `Ctrl-a` selects all visible nodes, and `Esc` clears the selection.
- Decide what selecting a parent means: does it select the whole subtree? If so, show partially selected parents with a tri-state marker such as `◐`.

## Accessibility and discoverability

- Show a one-line hint bar at the bottom (`←→ fold  ↑↓ move  / search  ? help`) and put the full key list behind `?`.
- Support both the arrow keys and vim keys. If you bind `h`/`j`/`k`/`l`, typeahead has to sit behind `/`.

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink, etc.), I can point out what its tree widget already handles and what you'd need to add.
