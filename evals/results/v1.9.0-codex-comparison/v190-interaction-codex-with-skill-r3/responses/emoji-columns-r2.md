**Use `WARN` / `OK`, or `!` / `✓`, for reliably aligned status columns.** Offer ASCII text as a fallback.

The issue is **terminal cell width**, which differs from string length:

- `✅` (U+2705) has a Wide base character and normally occupies **2 cells**.
- `⚠️` combines `⚠` (U+26A0) with an emoji presentation selector (U+FE0F). Terminals and width libraries can disagree about whether that sequence occupies **1 or 2 cells**.

If your padding assumes two cells but the terminal advances one, the next column shifts.

What to do:

1. **Measure display cells**, using a maintained, grapheme-aware terminal width library. Don’t pad using byte counts, code-point counts, or ordinary string length. Exclude ANSI color sequences from measurement.
2. **Prefer words or plain text symbols.** Use `✓` without an emoji selector; `OK` and `WARN` are the most portable. Optional color can reinforce the status.
3. **If keeping emoji**, prefer Wide-base emoji, test your supported terminals—including tmux—and provide an explicit `--ascii` or `--no-emoji` option. A width library cannot guarantee agreement with every terminal.
4. **Truncate other fields rather than wrapping table rows.** At 80 columns and in a 60-column split, preserve status and the main identifier; hide lower-priority columns.

A portable result needs no extra icon alongside the status word:

```text
STATUS  NAME
WARN    worker-1
OK      worker-2
```