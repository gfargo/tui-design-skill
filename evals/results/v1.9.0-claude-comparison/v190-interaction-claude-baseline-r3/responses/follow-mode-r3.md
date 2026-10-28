The usual pattern is "follow mode": the view sticks to the bottom until the user scrolls away, then stays where they put it.

## Core rules

1. **Following is on by default.** While the viewport is at the bottom, new lines scroll it along.
2. **Any upward scroll stops following.** That includes ↑, PgUp, `k`, mouse wheel up and search jumps. After that, new lines are added to the buffer but the viewport doesn't move.
3. **Getting back to the bottom resumes following.** If the user scrolls down to the last line, turn following back on. Also give them an explicit key for it: `G`, `End` or `F` (like `less +F`).
4. **Base it on position, not a flag set by key presses.** Compute `following = (offset + viewportHeight >= totalLines)` after every scroll action. This avoids state that can drift out of sync with what's on screen.

## What makes it pleasant to use

- **Keep the content still while paused.** Anchor the viewport to a line index, not to a distance from the bottom. Otherwise the text drifts as lines arrive. If you have a ring buffer that drops old lines, shift the anchor down by the number dropped. If the line they were reading gets evicted, clamp to the top and show a notice.
- **Show that it's paused.** Put an indicator in the status bar, like `⏸ PAUSED · 142 new lines · G to resume`. A count of unseen lines tells the user how far behind they are, and it's the most useful single thing you can add.
- **Pause while searching or selecting.** Search mode or a text selection should stop following, even if the user is technically at the bottom. Text moving under the cursor during a copy is very frustrating.
- **Throttle redraws.** Batch incoming lines and render at about 30–60 fps at most. At high log rates, redrawing on every line will spike CPU and cause flicker.
- **Handle resizes.** If the user was following before a resize, keep them at the bottom. If they were paused, keep the top visible line the same.
- **Handle wrapped lines.** If long lines wrap, do the "at bottom" check in wrapped rows, not log lines. Otherwise the check is off by a few rows and following won't resume reliably.

## Optional extras

- A pause toggle (`Space` or `p`) that stops following without scrolling, for when the user just wants the screen to hold still.
- A short grace zone of 1–2 lines from the bottom that still counts as "at bottom", so a small scroll doesn't accidentally pause.

## Minimal state

```
lines[]         // ring buffer
topLine         // index of first visible line
following bool  // derived after each scroll op
unseen int      // incremented on append while !following, reset on resume
```

On append: if `following`, set `topLine = max(0, len - height)`; otherwise increment `unseen`.

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink, etc.), I can sketch this using its viewport component. Several of them already include a "sticky bottom" helper you can build on.
