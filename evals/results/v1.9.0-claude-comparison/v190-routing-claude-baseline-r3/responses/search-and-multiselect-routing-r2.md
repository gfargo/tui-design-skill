## What `/` should do

**`/` should focus the filter box.** Users already expect this from vim, less, htop, lazygit, and k9s. Treat filtering as a separate mode:

- **List mode** (default): every key is a command (`j`/`k`, `space`, `d`, etc.).
- **Filter mode** (after `/`): keys type into the box, and the list narrows live as you type.
  - `Enter` keeps the filter and returns to list mode. Show the active filter in the header or footer, e.g. `filter: foo  (12/340)`.
  - `Esc` cancels and puts back whatever filter was there before you pressed `/`.
  - `↑`/`↓` (or `Ctrl-n`/`Ctrl-p`) still move the cursor, so users can filter and pick without leaving the box.
- In list mode with a filter applied, `Esc` clears the filter.

Decide whether `/` **filters** (hides non-matches) or **searches** (jumps to a match, then `n`/`N` for next/previous). Don't let it do both. You have a filter box, so make it filter.

If you'd rather have an always-focused filter like fzf, that works too. But then plain letters can't be commands, and every action needs `Ctrl`/`Alt` chords. For a list where users take actions on items, the `/` mode is the better choice.

## Multi-select with a filter

1. **Track selection by item ID, not by row.** The filter changes what's on screen, but it should never change what's selected.
2. **Keep selections when filtering.** Items you selected stay selected even when the filter hides them. Show this: `5 selected (2 hidden)`.
3. **Toggle keys:** `Space` in list mode. In filter mode `Space` is a typed character, so use `Tab`, as fzf does (`Shift-Tab` to toggle and move up).
4. **Bulk ops apply to visible items only.** "Select all" (`a` or `Ctrl-a`) and "invert" act on the filtered rows. This is what makes "filter then select all" useful. Say so in the help text.
5. **Actions apply to everything selected, including hidden items.** If any are hidden, say so in the confirmation: `Delete 5 items? (2 not shown by current filter)`. That way nobody deletes things they can't see by accident.
6. **Cursor:** when the filter changes, keep the cursor on the same item if it's still visible. Otherwise move it to the first match. If nothing is selected, actions apply to the item under the cursor.
7. **Make `Esc` undo one layer per press:** close filter mode, then clear the filter, then clear the selection, then leave the view. Never clear the selection and the filter with a single press.

## Keymap summary

| Key | List mode | Filter mode |
|---|---|---|
| `/` | open filter | types `/` |
| `Space` | toggle selection | types space |
| `Tab` | toggle + move down | toggle + move down |
| `a` / `Ctrl-a` | select all visible | `Ctrl-a` only |
| `Enter` | open/act | keep filter, back to list |
| `Esc` | clear filter, then selection, then exit | cancel edit |
