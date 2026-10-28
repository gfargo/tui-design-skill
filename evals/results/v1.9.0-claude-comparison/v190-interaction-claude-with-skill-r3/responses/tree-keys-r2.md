A tree view needs one rule for left and right arrows, expansion state that survives refreshes, and lazy loading that only shows activity on the row being expanded. Most of the rest (moving the cursor, filtering, marking rows, backing out) should work the same way as your other list views.

## Keys

The arrows and `h`/`l` do different things depending on the row. The skill's reference (`interaction-patterns.md` → *Tree views*) defines it like this:

| Key | On a folder | On a leaf (or a collapsed child) |
|---|---|---|
| `→` / `l` | Expand; if it's already open, move to its first child | Open or activate it |
| `←` / `h` | Collapse | Move to the parent |
| `Enter` | Toggle open/closed, or run the folder's own action if it has one | Open or activate it |

Pressing `←` repeatedly therefore walks up the tree, and pressing `→` repeatedly walks down into it. Users of file trees, ranger and yazi expect this.

The usual list keys apply too:

| Key | Action |
|---|---|
| `↑`/`↓`, `k`/`j` | Move one row through the visible rows |
| `PgUp`/`PgDn`, `Ctrl+U`/`Ctrl+D` | Move a page / half a page |
| `g`/`G`, `Home`/`End` | Jump to the top / bottom |
| `/` | Filter the tree (see below) |
| `Space` | Mark the row for a batch action (with a `*` prefix) |
| `Esc` | Clear the filter or marks, then go back. It never quits. |
| `q` | Go back one level; quit only at the root |
| `?` | Help |
| `r` | Refresh |

Optionally, add keys that expand or collapse a whole subtree. This is my suggestion, not a convention the reference sets. Don't put it on `*`, which the reference suggests for inverting marks.

## Behaviors

- **Indent 2 cells per level and draw connector lines** (`├─ └─`). Fall back to `|-` and `` `- `` when Unicode isn't reliable.
- **Load children lazily**, with a spinner on the row being expanded rather than across the whole app. Expansion shouldn't freeze the UI, and a failure should appear on that row, e.g. `▸ logs/  ✗ permission denied`.
- **Track expansion and selection by a stable ID** (path, key, UID), not by row number. Re-apply it after every refresh, sort or filter.
  - If the selected node disappears, select its nearest surviving neighbor, not the top row.
  - Don't let the view scroll out from under the cursor when rows above it appear or vanish.
- **Keep the parents of matches visible while filtering.** Show every ancestor of a match and expand it, even if the ancestor doesn't match. Without the parents, the matches lose their context. Show a count (`12/4,310`) and highlight the matched text. `Esc` clears the filter and puts back the user's earlier expansion state.
- **Keep the cursor 3 rows from the edge** while scrolling, and show the position in the panel title, e.g. `Files 42/1,203`.
- **Mouse is optional.** Clicking an arrow can toggle a folder, but everything must work from the keyboard.

## Layout, wide vs. 60 columns

```
Wide (120 cols)                                   60-col tmux split
┏━ Files 42/1,203 ━━━━━━━┓┌─ Preview ──────────┐  ┏━ src/ui/widgets ━━━ 42/1,203 ━┓
┃ ▾ src                  ┃│ fn render(...) {   │  ┃ ▾ widgets                       ┃
┃ ├─ ▾ ui                ┃│   ...              │  ┃ ├─ tree.rs                      ┃
┃ │  ├─ ▸ widgets        ┃│                    │  ┃ ├─ list.rs                      ┃
┃ │  └─   app.rs         ┃│                    │  ┃ └─ ▸ util  ⠋                    ┃
┃ └─ ▸ net  ⠋            ┃│                    │  ┃                                 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━┛└────────────────────┘  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
 →/l open  ←/h parent  / filter  space mark  ? help    →/l open  ←/h up  / filter  ? help
```

At 60 columns:
- The tree takes the whole width and the preview opens on demand (`Enter` or `o`).
- When nesting pushes names off the edge, start the tree at a deeper folder and show the full path in the title, as in the sketch, so names don't get cut off by indentation.
- Truncate names with `…` at the end rather than wrapping them.

## Keep the rows uncluttered

Trees tend to say "this is a folder" four times: the `▸`/`▾` arrow, the connector lines, a folder icon and a folder color. The arrow and the indentation are enough. Drop the icon, or treat it as optional Nerd Font decoration, and don't let color carry any meaning on its own.

## Consider other layouts

- **Side-by-side columns (like ranger or yazi):** better when users browse deep folder structures and need parent context plus a preview. They don't work well below about 80 columns.
- **A search picker (like helix):** better when users usually know what they're looking for and type to find it rather than browse.

If you tell me your framework (Bubble Tea, Ratatui, Textual, Ink…), I can point you to its tree widget or show how to build the key handling and ID-based expansion state in its style.
