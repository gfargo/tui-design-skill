Those symbols don’t have a consistent display width across terminals. `⚠️` includes a variation selector requesting emoji presentation; terminals may render it as one or two cells. `✅` is commonly two cells, but behavior varies with the terminal, font, and Unicode version.

If your table pads using string length, the problem gets worse: **character count isn’t terminal cell width**.

What to do:

- **Most reliable:** use ASCII statuses such as `[!]` and `[OK]`, padded to the same width.
- **If you keep emoji:** use a terminal-aware table library that measures display cells, handles grapheme clusters, and ignores ANSI color escapes. Raw `len()` or ordinary string padding won’t suffice.
- **Provide an ASCII mode:** width libraries and terminals can still disagree about emoji widths.

Removing the variation selector from `⚠️` to get `⚠` may help in some terminals, but it isn’t a portable fix.