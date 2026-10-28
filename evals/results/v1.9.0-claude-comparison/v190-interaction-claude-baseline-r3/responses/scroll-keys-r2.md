The working directory is empty, so I can't see your list view yet. Here's what I'd recommend for a typical terminal (TUI) list. Share the code or framework if you want it adapted.

## Scrolling keys

**Core keys (always include):**
| Key | Action |
|---|---|
| `↑` / `k` | Move up one item |
| `↓` / `j` | Move down one item |
| `PgUp` / `Ctrl-b` | Page up |
| `PgDn` / `Ctrl-f` / `Space` | Page down |
| `Home` / `g` | Jump to first item |
| `End` / `G` | Jump to last item |

**Worth adding:**
- `Ctrl-u` / `Ctrl-d` scroll half a page. Vim and less users expect this.
- `/` filters or searches, with `n`/`N` for the next and previous match, if the list can get long.
- Mouse wheel scrolling, if your framework supports it. Scroll the viewport by about 3 lines, and keep the selection inside the visible area.

**Behavior details that matter more than the keys themselves:**
- **Keep a scroll margin.** Keep the cursor 2–3 rows from the top or bottom edge so the user can see what's coming next.
- **Page moves keep one row of overlap,** so the user doesn't lose their place.
- **Don't wrap by default.** Pressing `↓` on the last item should stop there. Wrapping to the top is disorienting in long lists.
- **Keep the selection after resizes and data refreshes.** Track it by item ID, not by index.

## Position indicator

Use a **count in the footer or status line** plus a **scrollbar only when the content overflows**:

```
 > item 42
   item 43
   item 44                                  █
   item 45                                  │
──────────────────────────────────────────────
 42/318  ·  ↑↓/jk move  PgUp/PgDn page  g/G ends  / filter
```

- **`42/318`** (selected / total) is the most useful thing you can show. If a filter is active, show `12/40 (318 total)`.
- **The scrollbar** is a one-column track on the right edge (`│` with a `█` thumb). Size the thumb by `visible/total` and position it by scroll offset. Hide the track entirely when everything fits.
- **Overflow hints** are an alternative if you can't spare a column: show `↑ 12 more` at the top and `↓ 263 more` at the bottom when content is cut off.
- **The key hint line** should be short and context-aware. Show it by default, and let `?` open the full help.

If you need something minimal, pick `n/total` in the footer. It answers both "where am I" and "how much is there" at no layout cost.

Tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink, etc.) and I can sketch the implementation.
