**Use `!` and `✓`, or `WARN` and `OK`, for a reliably aligned status column.** Offer ASCII text as a fallback.

The problem is **terminal cell width**, which differs from string length:

- `✅` has a wide base character and normally occupies **2 cells**.
- `⚠️` is `⚠` (U+26A0) plus an emoji variation selector (U+FE0F). Terminals and width libraries can disagree about whether that sequence occupies **1 or 2 cells**.

If your padding assumes one width and the terminal uses another, every following column shifts.

To fix it:

1. **Measure display cells**, using your framework’s grapheme-aware, ANSI-aware width utilities. Don’t pad using bytes, code-point counts, or ordinary string length.
2. **Prefer text status markers.** Keep one non-color cue, optionally reinforced by color; replacing the emoji avoids adding redundant decoration.
3. **If retaining emoji**, reserve two cells, use consistent wide-base emoji where possible, and test supported terminals—including inside tmux. A width library alone cannot guarantee agreement with every terminal.
4. **Verify narrow layouts:** at 80×24 and 60 columns, retain status and the primary name; truncate names or hide secondary columns rather than wrapping table rows.

Don’t fix this by adding a hardcoded space after `⚠️`: that compensates for one terminal’s behavior and breaks another’s.