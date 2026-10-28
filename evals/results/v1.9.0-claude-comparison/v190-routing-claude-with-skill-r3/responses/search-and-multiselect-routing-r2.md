**Short answer:** In a list, `/` should **filter**: it narrows the rows shown to the ones that match. It shouldn't be a jump-to-match search. Multi-select depends on who owns typed keys. When the list has focus, **Space** marks a row. While the filter box has focus, Space is part of the query, so **Tab** marks the row instead.

## What `/` does

In a list, `/` filters, as in k9s and lazygit. In documents and logs, `/` searches and `n`/`N` move between matches. The focused view decides which one applies.

What the filter needs to do:
- Update as the user types, in under 100 ms. Anything slower feels broken.
- Show a count of matches against the total, e.g. `12/4,381`.
- Highlight the matched part of each row.
- Use smart-case: an all-lowercase query ignores case, and a query with any capital letter matches case.
- Rank exact matches first, then prefix matches, then substring matches.
- `Enter` keeps the filter and returns focus to the list. `Esc` clears it.

## Multi-select with a filter box

There are two ways to build this, and the key bindings follow from which one you pick.

**A. The filter box opens on `/`** (the right default for a full-screen list view)
- Pressing `/` puts focus in the box, and `Enter` sends focus back to the list with the filter still applied.
- While the box has focus, use `↑`/`↓` or `Ctrl+J`/`Ctrl+K` to move and `Tab` to mark. Tab marks the row and moves down; Shift+Tab marks and moves up. In this state Tab no longer moves focus between panels.
- When the list has focus, `Space` toggles the mark and `j`/`k` work again.

**B. The filter box always has focus** (an fzf-style picker you open, choose from, and close)
- Every printable key goes into the query, so `Tab`/`Shift+Tab` are the only marking keys.

**Rules for either version:**
- **Store marks by stable ID**, not by row position. A mark must still be there after the query changes, the list re-sorts or the data refreshes. Filtering a row out hides it but keeps its mark.
- **Show marks that the filter is hiding.** Put something like `3 marked (1 hidden)` in the footer. An action key such as `d` applies to *every* marked row, so its confirmation should give the total count, including hidden rows. Otherwise the user can delete something they can't see.
- **Use `*` as the mark**, with an accent background as a second cue. Don't rely on color alone. Unmarked rows get a blank instead of a `[ ]` box, because a symbol on every row tells the user nothing.
- **Esc, one step per press:** the first press clears the query, and the next leaves the filter box. I'd make marks survive a stray Esc and clear them with a later Esc at the list root or an explicit key. Losing a careful 20-item selection to one keypress is the worst outcome here.
- **Select all or invert:** `Ctrl+A` is the prefix key in GNU screen (and many tmux setups) and start-of-line in a text field, so also offer a printable key such as `*`. Never use `Ctrl+I`, because terminals send it as Tab.

## Layout

```
80 cols
┌ Items ──────────────────────────────────────── 12/4,381 ┐
│ /conf▏                                                  │
│ * app.config.ts                                          │
│ > config/                       ← cursor row (reverse)   │
│ * conftest.py                                            │
│   ...                                                    │
└──────────────────────────────────────────────────────────┘
 3 marked (1 hidden)  tab mark  enter keep  esc clear  d delete

60 cols
 /conf▏                                      12/4,381
 * app.config.ts
 > config/
 * conftest.py
 3 marked (1 hidden) · tab mark · esc clear · ? help
```

**At 60 columns:** drop the border. The filter line and the count carry the same information. The hint line shrinks to the marked count, the marking key, Esc and `?`. Clutter check: at most one border, and the mark is shown two ways (`*` plus the accent background), which is enough.

If you tell me the framework (Bubble Tea, Ratatui, Textual or Ink), I can show how that library handles focus and key routing for this.
