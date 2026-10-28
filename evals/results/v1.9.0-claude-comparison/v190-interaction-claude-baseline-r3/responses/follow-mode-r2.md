Use the **"sticky bottom"** pattern. Most good log viewers use it (`less +F`, `tail -f` in tmux copy mode, k9s, lazygit, browser devtools).

## Core rule
**Auto-scroll only while the viewport is at the bottom.** When the user scrolls up, pause following. When they get back to the bottom, resume.

```
follow = (scrollOffset == maxScrollOffset)   // recompute after every user scroll
on new lines:
    append to buffer
    if follow: scrollOffset = maxScrollOffset
    else:      unseen += n                    // don't move the viewport
```

Use a separate `follow` flag instead of checking position each time you append. Otherwise a burst of lines can arrive between the user's keypress and the next render, and the view gets yanked back down.

## While the user is reading
- **Keep the viewport still.** Anchor it by line index, not by "distance from bottom," so new lines appended below don't shift what's on screen.
- **Handle buffer trimming.** If you use a ring buffer with a max line count, lowering `scrollOffset` by the number of dropped lines keeps the view still. If the line they're reading gets evicted, clamp to the top and show a brief "older lines discarded" notice.
- **Show that following is paused.** Put an indicator in the status bar or bottom border, such as `⏸ PAUSED · 142 new lines ↓` or `-- FOLLOW OFF --`. Without it, users think the stream has died.
- **Give an explicit way to resume:** `G` / `End` / `F` jumps to the bottom and turns follow back on. Many viewers also let `f` toggle follow manually.

## Details that matter
- **Wrapped lines:** compute "at bottom" in visual rows, not log lines, or a long wrapped final line will break follow detection.
- **Search and selection:** while a search is active or text is selected, keep follow off even if the match happens to be on the last line.
- **Resize:** if follow is on, re-pin to the bottom after a resize. If it's off, keep the top visible line where it is.
- **High throughput:** batch appends and render at a capped rate (about 30–60 fps). Rendering on every line burns CPU and flickers.
- **Filtering:** apply filters to the visible view, and count `unseen` against the filtered lines only.

## Key bindings
| Key | Action |
|---|---|
| `↑`/`k`, `PgUp`, mouse wheel up | scroll, which turns follow off |
| `G` / `End` | jump to bottom, turn follow on |
| `g` / `Home` | jump to top (follow off) |
| `f` | toggle follow explicitly |

If you share your framework (Bubble Tea, Ratatui, Textual, Ink, etc.) or the existing viewer code, I can show how this fits into its viewport component.
