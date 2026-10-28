Terminals measure text in **display cells**, not characters. `⚠️` contains a warning symbol plus an emoji variation selector; terminals may render it as one or two cells. `✅` is usually two cells, but behavior varies by terminal, font, and Unicode version.

To keep columns aligned:

- **Most reliable:** use ASCII statuses such as `[!]` and `[OK]`, padded to the same width.
- **If you keep emoji:** pad using a terminal display-width library (`wcwidth` in Python, `string-width` in JavaScript), rather than string length. Strip ANSI color codes before measuring, or use a library that handles them.
- **For broad terminal support:** offer an ASCII mode. Width libraries cannot fully account for every terminal’s emoji rendering.

Removing the variation selector from `⚠️` may change its appearance, but it won’t guarantee consistent alignment.