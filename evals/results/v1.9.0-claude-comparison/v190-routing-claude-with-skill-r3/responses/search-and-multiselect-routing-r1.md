**`/` should filter the list.** In a list, `/` narrows what's shown, the way k9s and lazygit do. In a document or log, `/` searches instead and `n`/`N` jump between matches. The focused view decides which one it does.

**For multi-select, the mark key depends on who has the keyboard.** When the list has focus, **Space** marks a row. When the filter box has focus, Space is part of the query, so **Tab** marks the row and moves down, and Shift+Tab marks and moves up (fzf does this in `--multi`). While the filter box has focus, Tab marks rows and no longer cycles focus.

## The flow

| State | Typing | Moving | Marking | Enter | Esc |
|---|---|---|---|---|---|
| **List focused** | letters are commands | `j`/`k`, arrows | `Space` | open / drill in | clear marks, then go back |
| **Filter focused** (after `/`) | goes into the query | arrows, `Ctrl+J`/`Ctrl+K` (not bare `hjkl`) | `Tab` / `Shift+Tab` | keep the filter, return to the list | clear the filter, return to the list |

- **Enter keeps the filter, Esc throws it away.** That way the user can type `/api`, press Enter, and then use `j`/`k`/Space on the narrowed list.
- **Esc undoes one thing per press.** Order: close the filter box → clear the filter → clear marks → go back. Never quit on Esc.
- **Save marks by a stable ID, not by row number.** Marks then survive the filter changing, refreshes, and re-sorting. A marked row that the filter hides is still marked.
- **Count hidden marks out loud.** Show `3 marked (1 hidden)` in the header. Any action on marked rows should name the full count: `Delete 3 items (1 not shown)? [y/N]`, defaulting to No. Otherwise a filter can hide what the user is about to delete.
- **"Select all" should mean "all matching."** Ctrl+A is GNU screen's prefix key and the shell's go-to-line-start key, so it can't be the only way. Offer a printable key too. Use `*` for invert, not `Ctrl+I`, which the terminal can't tell apart from Tab.

If the box is always live (an fzf-style picker with no `/` step), `/` is just a query character. Tab is the only mark key, and there is no Space marking.

## Layout at 60 columns

```
 /api█                               12/340 · 3 marked (1 hidden)
 ───────────────────────────────────────────────────────────
 * api-gateway      running   2d
 ▌api-auth          running   5h      ← cursor: reverse video
 * api-billing      stopped   1d
   api-search       running   3h
 ───────────────────────────────────────────────────────────
 Tab mark  ↑↓ move  Enter keep  Esc clear             ? help
```

At wider sizes, add columns or a preview pane on the right. At 60 columns, drop the less important columns first. Shorten names with `…` instead of wrapping them, and keep the match count and mark count in the header.

## Other details

- **The footer hints must change with focus.** In the list they show `Space mark`. In the filter box they show `Tab mark`. If the footer is wrong, users press Space and get a space in their query.
- **Use only two cues for a marked row.** `*` plus an accent background, with nothing on unmarked rows. If every row has a marker, the marker means nothing. The cursor gets reverse video, so you don't need a third symbol for it.
- **The filter must feel instant.** Update in under 100 ms and highlight the matched text. Use smart-case: a lowercase query ignores case, and a query with any capital letter matches case exactly.

These come from the skill's `interaction-patterns.md`: the *Search and filter*, *Multi-select*, and *Esc, q, and Ctrl+C* sections, and *The fzf pattern in detail*.
