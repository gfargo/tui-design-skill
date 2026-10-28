The workspace is empty, so I can’t point to specific files. Look in two places:

- **Status bar component and animation/update loop:** find the spinner state, timer/tick handler, and render function. Advance the spinner on ticks, request a redraw, and stop ticking when idle. Keep its allotted width constant so nearby text doesn’t jump.
- **Table layout and text utilities:** find column measurement, padding, truncation, and wrapping. All four must use **terminal display width**, not byte count or string length.

The width rules:

| Content | Typical terminal width |
|---|---:|
| ASCII character | 1 cell |
| CJK character | 2 cells |
| Combining mark | 0 additional cells |
| Emoji | Often 2 cells; terminal-dependent |
| ANSI color/style escape | 0 cells |

Treat emoji sequences and accented characters as **grapheme clusters**: never split them during truncation. Measure the entire cluster with a terminal-aware Unicode width library; summing individual code-point widths can miscount joined emoji.

Apply the same width calculation everywhere, including headers, padding, borders, spinner frames, and ellipses. Strip or ignore ANSI escapes when measuring, and normalize tabs/newlines before laying out cells. If alignment still differs across terminals, check the library’s Unicode version and the terminal’s emoji and ambiguous-width settings.