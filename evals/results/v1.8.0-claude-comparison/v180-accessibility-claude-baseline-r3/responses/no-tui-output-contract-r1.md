I couldn't find any source files in the working directory, so this is a design answer, not a code change.

## Why the current output doesn't help

A table without borders is still a table. A screen reader reads one line at a time, so the user hears something like:

> "api dash server running 42 1.2G 3d4h db failing 97 3.8G 0d0h…"

The column headers were read once, at the top, and the user has to remember which number goes with which column. Padding spaces are either read aloud or skipped, and either way they add nothing. Colors, sparklines (small inline charts), ▲▼ arrows and spinners are lost or read as nonsense. Also, it's a one-time snapshot. The reason to have a dashboard is that it updates, and this output doesn't.

## What `--no-tui` should do

**1. Put labels on every value, one item per line.** Each line should make sense heard on its own:

```
Summary: 12 services, 10 running, 2 failing (db, cache). Updated 14:02:31.

Failing:
db: failing for 3 minutes. CPU 97 percent. Memory 3.8 GB of 4 GB. Last error: connection refused.
cache: failing for 40 seconds. CPU 0 percent. Memory 0.1 GB.

Running:
api-server: running for 3 days 4 hours. CPU 42 percent, rising. Memory 1.2 GB.
...
```

- **Put the summary first.** The user shouldn't have to listen to all 12 rows to learn that 2 are broken.
- **Sort by importance**, with problems first, and use headings that include counts.
- **Use words instead of visuals.** A color becomes "failing", ▲ becomes "rising", a sparkline becomes "rising, 30 to 45 over 5 minutes", and "3d4h" becomes "3 days 4 hours". Avoid cryptic abbreviations like `CPU%` or `RSS`.
- **Use no ANSI escape codes** (color or cursor movement), no `\r` progress bars, no spinners, and no box-drawing or braille characters.

**2. Add a live mode that only adds new lines.** Something like `--no-tui --watch` prints the summary once, then one line per change:

```
14:03:10 db: status changed from failing to running.
14:03:45 api-server: CPU crossed 90 percent.
```

Screen readers handle new lines appended at the end well, but they can't follow a screen that redraws itself. Report only real changes or crossed thresholds, debounce them, and don't reprint the whole state on every update. Keep the one-time snapshot as the default and make watching opt-in.

**3. Give the TUI's actions a non-TUI path.** If the dashboard lets you filter, drill into an item, or restart something, add flags or subcommands for each (`--filter db`, `status db`, `restart db`). Another option is a simple line-by-line prompt that uses normal line editing, not raw terminal mode.

**4. Add a separate machine-readable format.** For example, `--format json` or `csv`. Many screen-reader users prefer to pipe output into tools they already know. Keep it separate from the human-readable format and don't try to make one output serve both.

**5. Make it easy to turn on.** Switch to plain mode automatically when stdout isn't a terminal or `TERM=dumb`, and respect `NO_COLOR`. Let users set it permanently with an environment variable or config setting (e.g. `MYAPP_NO_TUI=1`) so they don't have to pass the flag every time. Document it in `--help`.

## Implementation note
Keep the dashboard's data separate from how it's drawn. The Ratatui view and the plain-text output should both read the same state struct. Write a plain renderer whose output is sentences, not rows, and a watcher that compares the previous state with the new one and prints only what changed. Don't reuse the table-layout code.

## Validate it
Test with VoiceOver on macOS (Cmd+F5 in Terminal), and with NVDA or Orca if you can. Then send the sample output above to the user who reported this and ask what they actually need from the dashboard. Usually it's "tell me when something breaks," which suggests `--watch` matters more than the snapshot.
