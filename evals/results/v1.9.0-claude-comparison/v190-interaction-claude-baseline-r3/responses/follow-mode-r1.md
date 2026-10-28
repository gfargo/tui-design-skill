The standard approach is **sticky-bottom ("follow") mode**. The view follows new output only while the user is at the bottom. As soon as they scroll up, it stops following, and it starts again when they come back down.

## Core rules

1. **Follow only when pinned.** Keep a `following` flag. It's true when the viewport's last line is the last log line.
2. **Any upward scroll turns follow off.** That includes arrow keys, PgUp, mouse wheel, `g`/Home, and jumping to a search match. Never move the viewport while `following` is false.
3. **Reaching the bottom turns follow back on.** Scrolling to the end or pressing `G`/End/`F` sets `following = true`. Don't make users press a separate "resume" key if they've already scrolled down manually.
4. **Keep the view still when lines are added.** While paused, new lines go below the viewport, so the text the user is reading must not move. Watch out for these:
   - **Line-count limits (ring buffer):** when old lines are dropped from the top, subtract the number dropped from your scroll offset. Otherwise the content slides up under the reader. If the line they were reading gets dropped, clamp the offset to 0 and show a hint like "older lines discarded."
   - **Line wrapping:** if you scroll by screen rows instead of log lines, a resize changes the row count. Anchor to a log line index plus a row offset within that line, not to a raw row number.

## Show the state

- Put a status indicator in a corner, such as `▼ FOLLOWING` or `⏸ PAUSED — 142 new lines (G to jump)`. The new-line count tells users how far behind they are.
- Optionally show a short "↓ new output" marker at the bottom edge when paused.

## Details that matter

- **Selection and search pause follow.** If the user is selecting text or has an active search match, don't scroll it away.
- **Throttle rendering, not data.** With heavy log output, add lines to the buffer right away but redraw at most every ~16–50 ms. This avoids flicker and keeps scrolling responsive.
- **Allow a small tolerance.** Treat "within 1 row of the bottom" as at the bottom, so a resize or a partly wrapped last line doesn't silently turn follow off.
- **Optional freeze key** (e.g. `Space`/`p`): pauses without scrolling, for when output is moving too fast to read.
- **Clear or filter:** after the content changes, keep the current follow state. If the user was following, stay pinned to the bottom of the new content.

## Minimal logic

```
on_append(lines):
    dropped = buffer.push(lines)        # ring buffer eviction count
    if following:
        offset = max_offset()
    else:
        offset = max(0, offset - dropped)
        unseen += len(lines)

on_scroll(delta):
    offset = clamp(offset + delta, 0, max_offset())
    following = offset >= max_offset() - TOLERANCE
    if following: unseen = 0

on_key_end():  offset = max_offset(); following = true; unseen = 0
```

This is how `less +F`, `tail -f` viewers in k9s and lazydocker, and most browser devtools consoles behave, so users will already know how it works. If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink, etc.), I can show how this fits its viewport component.
