Don't make `--no-tui` a picture of the dashboard. Make it a separate linear interface. It should never take over the screen and never repaint. It should print labelled `Field: value` lines with a summary first and a status line last. In watch mode it should print only what changed, as new lines. And every action the TUI has should also exist as a subcommand or flag.

## Why the borderless table still fails

- **Columns only make sense if you can see them.** A screen reader reads a row as "api-gateway degraded 82 1.2k 3". Without the header in view, the listener has to remember what column four means.
- **Sparklines and gauges become symbol noise.** `▁▃▅▇` and `████░░` get read out one character at a time, or skipped.
- **Status probably relies on color or a glyph.** Neither of those is spoken as a word.
- **It's a snapshot that then exits.** Restart, filter, drill-down and acknowledge all still require the TUI. That's the real gap.

## What it should output

A one-shot snapshot (`myapp --no-tui`):

```
Dashboard: prod-cluster. 12 services, 2 need attention. Updated 14:02:31.

warning: 2 services need attention.

Service 1 of 12: api-gateway
  Status: degraded
  CPU: 82 percent, rising from 40 percent over 5 minutes
  Requests: 1,200 per second
  Errors: 3 in the last minute

Service 2 of 12: billing-worker
  Status: down since 13:58
  Last error: connection refused to postgres-primary. Check the database, then run: myapp restart billing-worker

Service 3 of 12: auth
  Status: healthy
  ...

Done. 12 services: 9 healthy, 2 degraded, 1 down.
```

The rules behind it:

- **Problems go first.** Sort by severity so the listener hears what matters without sitting through ten healthy services.
- **Every line is labelled.** Use `Field: value`, plus `error:` and `warning:` prefixes, so the listener knows what a line is before hearing it.
- **Charts become sentences.** Give the latest value, the trend and the range ("rising from 40 to 82 percent"). No block characters, box drawing or emoji.
- **State is a word.** Write "degraded", not a yellow dot. Color can stay as a bonus, but nothing should depend on it.
- **Nothing is truncated.** Truncation is only there to fit the visual layout; in plain mode print full values.
- **Errors say what to do next.** Write them so they make sense read aloud: what failed and what to run.
- **The last line is a status line,** so the user knows output is complete.

Watch mode (`myapp --no-tui --watch`) appends only changes. It never re-prints the full table on a timer and never shows a spinner:

```
14:03:10 api-gateway: status changed from healthy to degraded.
14:05:42 billing-worker: recovered. Status: healthy.
```

## Actions

- **One-shot commands:** turn each TUI action into a command, e.g. `myapp show api-gateway`, `myapp restart billing-worker --yes`, `myapp ack api-gateway`, `myapp --no-tui --filter status=degraded`.
- **Interactive mode, if you keep one:** use numbered choices read as typed input, not an arrow-key menu (which gets re-read every time the highlight moves):
  ```
  Choose an action for billing-worker:
  1. Show details
  2. Restart
  3. Acknowledge
  Enter a number:
  ```
- **Unattended runs:** every prompt also needs a flag (`--yes`, `--action restart`) so plain mode can run without input.

## Streams, formats and switching it on

- **Streams:** results go to stdout. Progress is one static line on stderr ("Fetching metrics…"), then the result. Exit codes are meaningful, e.g. non-zero when something is down if scripts depend on that.
- **Formats:** support `--format text|csv|json|ndjson`. `text` is the format above. Some screen-reader users like CSV because they can open it in a table-aware tool. JSON and NDJSON are for scripts.
- **Switching it on:** it shouldn't need passing every time. Accept `--no-tui`, an env var like `MYAPP_PLAIN=1`, or a config key such as `ui.mode = "plain"`. Also turn it on automatically when stdout isn't a terminal. Don't try to detect screen readers, because it isn't reliable; gh's `GH_ACCESSIBLE_PROMPTER` and Claude Code's screen-reader mode both use explicit opt-in.

## Ratatui implementation

Ratatui has no accessibility layer (the tracking issue is ratatui#2610), so this has to be a separate code path, not a different widget style:

```rust
let plain = cli.no_tui
    || std::env::var_os("MYAPP_PLAIN").is_some_and(|v| !v.is_empty())
    || config.ui.plain
    || !std::io::stdout().is_terminal();

if plain {
    return plain::run(&cli, &client); // never calls ratatui::init()
}
let terminal = ratatui::init();
```

- **No raw mode, no alternate screen, no hidden cursor.** Plain output should just scroll normally.
- **One shared model.** Have the Ratatui view and the plain renderer read the same data struct, and make the renderer a pure function that writes to any output, such as `fn render_text(&Snapshot, &mut impl Write)`. Then the two can't drift apart and the text output is easy to golden-test.
- **A coverage test.** Loop over the TUI's action enum and check that each action maps to a plain-mode command. That way "nothing is TUI-only" is enforced, not just hoped for.
- **Golden-test the text output** for the healthy, degraded, down, empty and disconnected states. Also check that `NO_COLOR` and piped output produce byte-identical text.

Finally, show the sample output above to the user who reported this before you build it out. They'll know quickly whether the order and labels work in their screen reader.
