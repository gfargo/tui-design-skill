Use the standard keys below and show a `42/1,203` count, right-aligned in the panel title. You don't need a scrollbar.

## Keys

| Keys | Moves |
|---|---|
| `↑`/`↓` and `k`/`j` | One row |
| `PgUp` / `PgDn` | One page, keeping one row of overlap so the user doesn't lose their place |
| `Ctrl+U` / `Ctrl+D` | Half a page |
| `Home` / `End` and `g` / `G` (or `gg` / `G`, vim-style) | Top / bottom |
| Mouse wheel | Scrolls the viewport under the pointer, not the selection |

Rules that go with them:
- **Scroll-off margin:** keep the cursor at least 3 rows from the top and bottom edges while it moves, so the next rows show up before the user reaches them. If the viewport is under 12 rows tall, use 1 row.
- **Letter keys stop while a text field is active.** If you have type-to-filter (`/`), `j`/`k`/`g`/`G` are typed as letters while the filter input has focus. Only the arrows, `PgUp`/`PgDn` and `Home`/`End` keep scrolling.
- **Mouse is optional.** Every scroll action must also work from the keyboard.

## Position indicator

Show `selected/total` with a thousands separator, right-aligned in the panel title (or in the footer if the list has no title):

```
 Packages ─────────────────────────────────── 42/1,203
   lodash          4.17.21   MIT
 ▶ react           18.3.1    MIT
   react-dom       18.3.1    MIT
```

- **When a filter is on,** count the filtered results and show the total next to it, e.g. `3/57 (of 1,203)`. Users need to know that rows are hidden.
- **A scrollbar is optional decoration.** The count already carries the meaning, screen readers can read it, and it takes no width away from the rows. If you add a scrollbar anyway, drop it first in narrow layouts.
- **Use a percentage only for documents.** It fits a pager or log better than a row count does.

## At the floor size (60 columns)

The count is short enough to stay. Shorten the title before you drop the count:

```
 Packages ──────────────────────── 42/1,203
 ▶ react          18.3.1   MIT
```

## If the list refreshes live

Track the selected row by a stable ID, not by its index. Then the count and the selection stay on the same item when rows are inserted above it. If the selected item disappears, move to its nearest neighbor instead of jumping to row 1.

If you tell me the framework (Bubble Tea, Ratatui, Textual, Ink), I can show how to wire these keys up and add the count.
