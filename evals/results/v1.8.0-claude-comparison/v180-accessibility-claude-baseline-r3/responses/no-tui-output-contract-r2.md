I didn't find any code in the working directory, so this is a design answer, not a patch.

## Why the borderless table doesn't help

Removing the borders doesn't change the real problem. The output is still laid out as a grid, and screen readers read text one line at a time. A row like this:

```
api-1      running    42%    3.1s    ▁▃▅▇
```

is read aloud as "api-1 running 42 percent 3.1 s" plus some noise for the sparkline characters. The listener has to remember the column headers from many lines earlier to know what "42%" and "3.1s" mean. The alignment spaces are meaningless to them, and any meaning carried by color or symbols (a red dot, a ▲) is lost. On top of that, the program prints once and exits. So `--no-tui` also takes away live updates and everything interactive, and the user ends up with less than sighted users get, not the same information in another form.

## What `--no-tui` should do

The goal is the same information and the same abilities, delivered as plain lines of text that make sense when read in order.

**1. Print labeled records, not a table.** Each line or block should make sense on its own, with a summary first:

```
3 services. 1 degraded, 2 healthy.

Service api-1: degraded. CPU 42 percent. p95 latency 3.1 seconds, up from 0.8.
Service api-2: healthy. CPU 12 percent. p95 latency 0.4 seconds.
Service worker: healthy. Queue depth 17.
```

- Put the most important fact (the status) right after the name, so users can skip ahead once they've heard enough.
- Use words for status, not color or glyphs. Write out units and trends ("up from 0.8", not "▲").
- Leave out box-drawing characters, sparklines, spinners and emoji.

**2. Keep live updates by appending events, not redrawing.** Add a `--watch` mode that prints only what changed, as new timestamped lines:

```
12:04:31 api-1 changed from healthy to degraded. p95 latency 3.1 seconds.
12:06:10 api-1 recovered. Now healthy.
```

- Never use `\r` overwrites, cursor movement or screen clears. Screen readers either miss those or re-read everything.
- Throttle or debounce the output. A metric that changes every 250 ms shouldn't produce a line every 250 ms. Report status changes and threshold crossings, plus an optional periodic summary (e.g. `--interval 60`).

**3. Make interactive features available another way.** Anything the TUI lets you do with keys (filter, sort, drill into a service, acknowledge an alert) needs an equivalent:
- flags or subcommands: `dash status --service api-1`, `dash status --only degraded`, `dash ack 1234`
- optionally, a simple line-based prompt (read a command, print the result). It should run in normal terminal mode, not raw mode.

**4. Don't touch Ratatui at all in this path.** Don't enable raw mode, don't enter the alternate screen and don't create a `Terminal`. Render straight from your shared data model to stdout with `println!`. If the current code sets up the terminal first and then prints, that alone can confuse screen readers.

**5. Follow standard terminal conventions:**
- Respect `NO_COLOR`.
- Turn plain mode on automatically when stdout isn't a TTY or `TERM=dumb`.
- Let users set it once in a config file or env var (e.g. `DASH_PLAIN=1`) so they don't have to pass a flag every time.
- Send errors to stderr in full sentences, with meaningful exit codes.

**6. Keep accessible output separate from machine output.** Add `--format json` (or csv) for scripts. It's useful to screen-reader users too, since they can pipe it to `jq` or open it in a spreadsheet. It shouldn't replace the readable mode, though.

**7. Naming:** consider calling the mode `--plain` or `--accessible` and keeping `--no-tui` as an alias. "No TUI" says what's removed, not what you get.

## Before you build it

Go back to the user who reported this. Ask which screen reader and terminal they use (VoiceOver with Terminal.app, NVDA with Windows Terminal and Orca behave differently), and what they actually use the dashboard for. If they mostly need "tell me when something breaks," the `--watch` event stream matters more than the snapshot. Then have them try a prototype of the output above before you polish it.
