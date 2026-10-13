The borderless table doesn't help because the problem was never the borders. A screen reader reads a terminal one line at a time, so any layout built on visual alignment falls apart. Your current output has these problems:

- **Values lose their headers.** A row like `web-01  92  4.1  ok  12s` gets read as "web-01 92 4.1 ok 12s", and the listener has to remember which column each number belongs to. The column alignment only works for someone who can see it.
- **It exits right away.** The point of a dashboard is to watch things change. A one-time snapshot means the user has to re-run it and compare the results from memory.
- **Glyphs and color carry meaning.** Sparklines, `●`, `▲` and `…` get read aloud as "black circle" or "up-pointing triangle", or skipped entirely. Red or green status with no word attached isn't conveyed at all.
- **Nothing is summarized.** A sighted user sees "everything's green except one row" at a glance. A screen-reader user has to listen to every row to find that out.

## What `--no-tui` should do

**1. Default: a linear, labeled snapshot, with a summary first.**

```
Summary: 12 services, 1 degraded, 0 down. Updated 14:02:11.

Degraded:
web-03: status degraded. CPU 92 percent, rising from 40 over 5 minutes. Memory 6.8 of 8 GB. Last check 12 seconds ago.

OK:
web-01: status ok. CPU 31 percent. Memory 4.1 of 8 GB. Last check 3 seconds ago.
...
```

- Put one item on each line, written as `label: value`, so every line makes sense on its own.
- Sort by severity so the important items come first.
- Turn sparklines and trend arrows into words, like "rising from 40 to 92 percent over 5 minutes".
- Write status as words, never as color alone, and don't truncate values.
- Use no box-drawing characters, spinners, progress bars or cursor movement.

**2. `--no-tui --watch`: an append-only stream of changes.** This is the part that actually replaces the dashboard. Never redraw or clear the screen. Print one line per meaningful event:

```
14:02:11 web-03 status changed from ok to degraded (CPU 92 percent).
14:05:40 web-03 recovered, status ok.
```

Only report changes and threshold crossings, not every tick. Group bursts of events together so the screen reader isn't flooded with announcements.

**3. Every TUI action needs a non-TUI equivalent.** If the TUI lets you filter, drill into an item, acknowledge an alert or restart something, expose those as subcommands, for example `dash show web-03`, `dash list --status degraded` or `dash ack 1234`. Otherwise `--no-tui` is a read-only, lower-tier mode.

**4. Keep machine output separate.** `--json` is for scripts and `--no-tui` is for people. Don't make the accessible mode also serve as the parseable format, because each one ends up worse at its job.

## Smaller details

- Let people turn the mode on persistently with a config setting or environment variable such as `DASH_NO_TUI=1`, so they don't have to type the flag every time. Also switch to it automatically when stdout isn't a TTY or `TERM=dumb`.
- Respect `NO_COLOR`. Send errors to stderr as plain sentences.
- Keep the order and wording of fields stable between runs, so users learn where to listen for what they need.

## Before you build it

Ask the user who reported this what they were trying to do: check overall health, wait for a particular change, or act on an alert. Their answer tells you whether the snapshot, the watch stream or the subcommands matter most. Then test the result with a real screen reader, such as VoiceOver in macOS Terminal, NVDA with Windows Terminal, or Orca on Linux, preferably with that same user.

I couldn't find any source files in the working directory, so this is design advice only. If you point me at the code, I can sketch how to separate the data model from the Ratatui rendering so all three output modes can share it.
