The working directory is empty, so I couldn't check your code. Here's what I'd recommend for a TUI list view, based on conventions most terminal users already know.

## Scrolling keys

| Action | Primary | Alternates |
|---|---|---|
| Move up / down one item | `↑` / `↓` | `k` / `j` |
| Page up / down | `PgUp` / `PgDn` | `Ctrl+b` / `Ctrl+f` |
| Half page up / down | `Ctrl+u` / `Ctrl+d` | — |
| Jump to first / last | `Home` / `End` | `g` / `G` |
| Select / open | `Enter` | — |
| Filter / search | `/` | then `n` / `N` for next/previous match |

Guidelines:
- **The arrow keys and PgUp/PgDn/Home/End must always work.** Vim keys are a bonus for power users, and new users shouldn't have to know them.
- **Paging should keep one line of overlap,** so a page moves by `visible_height - 1` and the user doesn't lose their place.
- **Don't wrap around.** Pressing `↓` on the last item should stay put. Wrapping makes it hard to tell where the list ends.
- **Keep the cursor away from the edges.** Start scrolling 2–3 rows before the cursor reaches the top or bottom so the user can see what's coming.
- **Support the mouse wheel** if your framework allows it. Have it scroll by about 3 lines without moving the selection, or move the selection, but pick one and stay consistent.

## Position indicator

Show the position in the footer or the right side of the title bar, formatted as **`12/340`** (selected item / total). It's precise, takes little space, and stays accurate when the list is filtered.

Additions worth making:
- **Show the filtered count when a filter is active:** `12/48 (340 total)`.
- **Add overflow hints** like `▲ more` / `▼ more`, or dim arrows at the top and bottom edges, so users can tell there's content off-screen.
- **Add a scrollbar** (a one-column track `│` with a thumb `┃` or `█`) only if you have a spare column and the lists are long. It shows proportion well but is redundant if you already have the counter.
- **Skip percentages** like `34%`. They're less useful than `n/total` for discrete items.

## Discoverability

Put a short hint line in the footer, for example `↑↓ move  PgUp/PgDn page  / filter  ? help`, and list the full keymap behind `?`.

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink, etc.), I can map these to its built-in list/viewport components or sketch the implementation.
