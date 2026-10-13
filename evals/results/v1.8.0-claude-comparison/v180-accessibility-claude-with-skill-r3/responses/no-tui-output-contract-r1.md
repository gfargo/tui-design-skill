Your users are right. A table without borders is still a table. The listener has to remember that the third column is "status" and count positions across every row. "Print and exit" also means they can't do anything the TUI lets them do: watch for changes, drill into an item, or take an action. `--no-tui` should be a full linear version of the dashboard, not a screenshot of it with the box-drawing removed.

## What `--no-tui` should do

**1. Turn rows into labelled records, with a summary first and a status line last.** A screen reader can read these lines in any order without needing to know the column order.

```
4 services: 2 healthy, 1 degraded, 1 down.

Service: api
Status: degraded
Latency p95: 840 ms
Error rate: 2.1 percent
Last deploy: 14 minutes ago

Service: worker
Status: down
Reason: health check failed 3 times
...

Done. Showing 4 of 4 services.
```

- Use words for status ("degraded"), not colors, ✓/✗ glyphs or column position. Write units out in full.
- Use no borders, separator rows, sparklines or ASCII art. A screen reader reads these out as symbol noise.
- End with a status line so the user knows the command succeeded. Silent success leaves them guessing.

**2. Offer machine formats as well:** `--format text|csv|json`. CSV lets a user open the data in a spreadsheet or browse it with their screen reader's table navigation. JSON is for scripts.

**3. Make every TUI action reachable.** Nothing should be TUI-only. Two good ways to do this:
- **Subcommands or flags:** `dash show api`, `dash restart worker --yes`, `dash list --status down`.
- **A numbered menu when interactive:** print `1. api  2. worker …  Choose a service:` and read a typed line. Don't use an arrow-key menu, because the screen reader re-reads it every time the highlight moves.

Every prompt needs a flag equivalent such as `--yes` or `--service api` so the mode can also run unattended.

**4. Append live updates instead of repainting.** The dashboard probably refreshes, so add `--watch`. It prints the snapshot once, then only the changes, each as a labelled line:

```
12:04:31 warning: api changed from healthy to degraded (p95 latency 840 ms)
12:06:02 info: api recovered, now healthy
12:07:45 error: worker is down. Health check failed 3 times. Run "dash logs worker" for details.
```

No spinners or progress bars, since these get read out character by character. For progress, print an occasional line like `Checked 3 of 10 services`. Prefix each line with its kind (`error:`, `warning:`, `info:`) so the listener knows what it is before hearing it. Write errors in plain words that say what failed and what to do next.

**5. Keep the streams separate.** Results go to stdout. Prompts, progress and diagnostics go to stderr. Use meaningful exit codes, for example non-zero if any service is down when that suits your domain.

**6. Make it easy to turn on, and keep it on.** Users enable it once and it stays enabled:
- the flag (`--no-tui`, perhaps with `--plain` as an alias);
- an environment variable, e.g. `DASH_PLAIN=1`;
- a config key, e.g. `plain = true`.

It should also switch on automatically when stdout is not a terminal. Don't try to detect a screen reader, because that isn't reliable. gh's `GH_ACCESSIBLE_PROMPTER` and `GH_SPINNER_DISABLED` env vars, with matching config keys, are a good model. Claude Code's screen-reader mode is a full published example of this output style.

## Ratatui implementation notes

Ratatui has no screen-reader support (this is tracked in ratatui#2610), so the plain mode is the accessibility answer. It should never enter raw mode or the alternate screen.

```rust
use std::io::{self, IsTerminal, Write};

fn plain_mode(cli: &Cli, cfg: &Config) -> bool {
    cli.no_tui
        || std::env::var_os("DASH_PLAIN").is_some()
        || cfg.plain
        || !io::stdout().is_terminal()
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();
    let cfg = Config::load()?;
    if plain_mode(&cli, &cfg) {
        return plain::run(&cli, &cfg); // never calls ratatui::init()
    }
    tui::run(&cli, &cfg)
}
```

```rust
pub fn print_snapshot(out: &mut impl Write, snap: &Snapshot) -> io::Result<()> {
    writeln!(out, "{} services: {}.", snap.services.len(), snap.summary_words())?;
    for s in &snap.services {
        writeln!(out)?;
        writeln!(out, "Service: {}", s.name)?;
        writeln!(out, "Status: {}", s.status.as_word())?;
        writeln!(out, "Latency p95: {} ms", s.p95_ms)?;
    }
    writeln!(out)?;
    writeln!(out, "Done. Showing {} of {} services.", snap.shown, snap.total)
}
```

- **Share the data layer.** Both renderers should read the same `Snapshot` or state model and the same action functions, so the plain mode can't fall behind the TUI. If the current `--no-tui` code calls the table-rendering code, that's the coupling to break.
- **Watch mode:** diff consecutive snapshots in the model layer and print only the transitions. Don't print a new full snapshot every tick.
- **Tests:** golden-test the plain output for these cases: an empty list, all healthy, mixed statuses, an error or disconnected state, and a very long service name. Also unit-test the snapshot diff that produces the `--watch` lines and the `plain_mode()` decision, including the non-TTY case.

**Before you ship it:** ask the user who reported the problem to try a build. The general rules above are well established, but they can tell you which actions they actually need and whether the labels make sense when spoken.
