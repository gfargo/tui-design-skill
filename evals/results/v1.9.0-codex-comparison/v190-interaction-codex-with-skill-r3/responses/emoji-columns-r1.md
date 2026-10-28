**Use `WARN` / `OK`, or `!` / `✓`, for a reliably aligned status column.** Emoji can occupy different terminal cell widths.

Your two symbols behave differently:

- `✅` (U+2705) has a wide base and normally occupies **2 cells**.
- `⚠️` is `⚠` (U+26A0) plus an emoji variation selector (U+FE0F). Terminals and width libraries can disagree on whether that sequence occupies **1 or 2 cells**.

If your app pads assuming one width and the terminal renders another, the following columns shift. Counting bytes, code points, or string length also gives incorrect padding.

What to do:

1. **Prefer words or narrow text symbols.** Offer an ASCII fallback such as `WARN` / `OK`. Optional yellow/green can reinforce the text; keep meaning without color.
2. **Measure display cells** using a maintained, grapheme-aware, ANSI-aware width library or your framework’s table renderer. Use that measurement for padding and truncation.
3. **If you keep emoji**, prefer wide-base symbols, test your supported terminals—including inside tmux—and retain an explicit text fallback. A width library cannot guarantee agreement with every terminal.

For example, at both 80 and 60 columns:

```text
NAME       STATUS
api        WARN
worker     OK
```

Keep status visible as space shrinks; truncate long names or hide secondary columns. Use one text status plus optional color—adding a checkmark alongside `OK` repeats the same information.