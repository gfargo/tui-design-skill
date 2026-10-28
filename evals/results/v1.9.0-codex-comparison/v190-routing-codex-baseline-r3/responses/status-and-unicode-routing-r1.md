The workspace is empty, so I can’t point to specific files. Look in these areas:

- **Status bar / loading indicator:** Find the spinner component, its timer or tick handler, and the code that starts and stops it. Animate only while work is active, stop the timer afterward, and reserve a fixed display width so changing frames don’t shift nearby text. Provide a static fallback for terminals without animation support.
- **Table layout / text measurement:** Find column sizing, padding, truncation, and wrapping. They must measure **terminal display cells**, not bytes, code points, or string length.

The width rules are:

- Most Latin characters occupy **1 cell**; most CJK characters occupy **2**.
- Combining marks generally add **0 cells**.
- Emoji may contain multiple code points joined into one visible grapheme; many occupy **2 cells**, but terminal behavior varies.
- ANSI color and styling sequences occupy **0 cells**.
- Truncate and wrap at **grapheme boundaries**, preserving complete emoji and combining sequences. Include any ellipsis in the width budget.
- Use the same terminal-aware width library for measurement, padding, wrapping, and truncation. Avoid hand-maintained character ranges.
- Expand tabs consistently or disallow them in table cells.

If alignment still differs after those fixes, check the terminal’s Unicode-width settings and font: the application and terminal must agree on character widths.