## What `/` should do

**`/` moves focus into the filter box.** That's the convention in less, vim, k9s, lazygit, and most other TUIs, so users will press it without thinking.

- **Enter** commits the filter and puts focus back on the list. The filter stays on and is shown in the header, e.g. `filter: foo (12/240)`. This lets people filter first and then act on the results.
- **Esc** while typing clears the query and puts focus back on the list.
- **Esc** in the list with a filter on clears the filter. Each Esc should undo one thing, not several at once.
- Pick one behavior: either `/` **filters** (hides rows that don't match) or it **searches** (jumps to the next match with `n`/`N`). Since you already have a filter box, make `/` filter. Don't add a second search mode.

## Multi-select with a filter

The main problem is that while the filter box has focus, every printable key is text. So Space and `x` can't toggle selection there. You have two options:

1. **Modal (recommended if you have single-letter keys).** Space or `x` toggles selection only when the list has focus. Users type a filter, press Enter, then select. This is simple and avoids conflicts.
2. **fzf-style (if the box always has focus).** Use **Tab** and **Shift-Tab** to toggle and move. Put actions on Ctrl keys or Enter. Leave all letter keys for the query.

Whichever you pick, these rules matter:

- **Store selection by item ID, not row index.** Selected items stay selected when the filter changes, including items the filter hides.
- **Show hidden selections**, e.g. `5 selected (2 hidden by filter)`. Otherwise people will run a bulk action on items they can't see.
- **Select-all (`a` or Ctrl-A) selects only the visible, filtered rows.** That's what people mean when they filter and then select all. Pair it with a matching "deselect visible."
- **Bulk actions apply to the whole selection.** If any selected items are hidden, the confirmation should say so: `Delete 5 items (2 not currently shown)?`
- **Clearing the filter doesn't clear the selection.** Keep that on its own key, or on Esc once the filter is already cleared.
- With nothing selected, actions apply to the row under the cursor. This makes single-item use work without selecting anything.

Example key map for the modal approach:

| Key | List focused | Filter focused |
|---|---|---|
| `/` | focus filter | literal `/` |
| `j`/`k`, arrows | move | arrows move the list cursor |
| Space | toggle select | literal space |
| `a` / `A` | select / deselect visible | literal |
| Enter | act on selection or cursor | commit filter, focus list |
| Esc | clear filter, then clear selection | clear query, focus list |

If you tell me which framework you're using (Bubble Tea, Textual, Ratatui, etc.) or point me to your list component, I can map this onto your code.
