Terminals align columns by **display cells**, while many table formatters count characters. Those counts differ for emoji:

- `⚠️` contains a warning symbol plus an invisible emoji variation selector.
- `✅` is a different Unicode symbol.
- Their displayed widths depend on the terminal, font, and Unicode support—often one or two cells.

To fix it:

- **Most portable:** use ASCII statuses such as `WARN` and `OK`, then pad them to a fixed width.
- **If you keep emoji:** use a terminal-aware width library, such as Python’s `wcwidth` or JavaScript’s `string-width`, instead of `len()` or `.length`. Strip or account for ANSI color codes when measuring.
- **For terminals you control:** standardize the terminal and font, and test there. Width libraries can still disagree with a terminal’s emoji rendering.

Adding spaces until it looks right in one terminal won’t reliably fix others.