## What `/` should do

Use `/` to **move focus into the filter box**. That's what it does in vim, less, man, k9s, lazygit, htop, and most other TUIs, so your users will already expect it.

- `/` focuses the filter input and the cursor moves there.
- **Enter** applies the filter and returns focus to the list. The filter stays active and stays visible, for example as `/foo` in the header or status line.
- **Esc** inside the input clears the filter and returns to the list. Esc in the list while a filter is active also clears the filter.
- Optionally, `n` and `N` in the list jump to the next or previous match. Only add these if you highlight matches instead of hiding non-matches.

This gives you two modes: **normal mode**, where letters are commands, and **filter mode**, where letters are text. That split is what lets multi-select work.

If your filter box is always live (any keystroke filters, like fzf), `/` is just a character you can type. In that case you can't use bare letters or Space as commands, so every action needs Tab, Ctrl, or Alt bindings. Choose one model. Most lists work better with the modal `/` approach. Always-live filtering suits pickers whose main job is find-and-pick.

## How multi-select works with a filter

**1. Key the selection by item ID, not by row index.** Filtering changes which rows are visible, not which items are selected. Selections made before you filter must still be there after you clear it.

**2. Use toggle keys that work in both modes:**

| Action | Normal mode | Filter mode |
|---|---|---|
| Toggle current item | `Space` (or `Tab`) | `Tab` (Space is text here) |
| Select all **visible** | `Ctrl-A` or `*` | `Ctrl-A` |
| Clear selection | `Ctrl-D` or `u` | `Ctrl-D` |
| Move cursor | `j`/`k`, arrows | arrows, `Ctrl-N`/`Ctrl-P` |

Tab for toggling in filter mode follows the fzf convention. That way you can type, Tab, keep typing, and Tab again without leaving the input.

**3. Select-all applies only to the visible (filtered) rows.** This is the main reason to filter at all: "show me `*.log`, select all, delete."

**4. Show selected items that the filter hides.** Put a count in the status line, for example `5 selected (2 hidden by filter)`. Without it, a bulk action can affect items the user can't see.

**5. Bulk actions apply to the whole selection, including hidden items. Confirm when hidden items are included:** "Delete 5 items? 2 are not currently shown." The other option, acting only on visible selected items, makes selection quietly depend on the filter, and that's harder to reason about.

**6. Keep the cursor steady while filtering.** If the item under the cursor still matches, keep the cursor on it. If not, move it to the first match. Don't reset to the top on every keystroke.

**7. Clearing the filter keeps the selection.** Esc clears the filter text, a second Esc (or `Ctrl-D`) clears the selection. Never clear both with one key, because losing a selection you built up is very annoying.

## Short version

`/` enters filter mode, Enter keeps the filter, Esc clears it. Tab toggles selection in either mode. Selection is stored by ID and survives filtering. Select-all covers only visible rows. The status line always shows how many selected items are hidden.
