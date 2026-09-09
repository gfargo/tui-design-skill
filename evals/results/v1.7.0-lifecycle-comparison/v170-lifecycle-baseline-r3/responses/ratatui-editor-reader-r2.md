Make terminal ownership exclusive: **the event reader must stop before Vim starts**, not merely stop forwarding its events.

1. Quiesce and await acknowledgement from the Crossterm reader; also stop rendering/output.
2. Restore the TUI’s terminal modes (including mouse/cursor settings): leave alternate screen, disable raw mode.
3. Spawn/wait for Vim. Vim is now the sole terminal input/output owner.
4. Always attempt TUI re-entry after Vim returns—even if spawning/waiting Vim failed or Vim returned a nonzero status.
5. On successful re-entry, clear/reset Ratatui’s buffer and do a full redraw, then restart the reader. Do not resume the reader if re-entry failed.

The reader is what steals Vim’s keys and terminal-query replies; those replies explain the ANSI/RGB “garbage.” Ratatui specifically calls out pausing advanced event handlers during external-editor handoff. Re-entering requires a clear/full redraw because Ratatui’s diff buffer is stale after the screen switch. [Ratatui Vim recipe](https://ratatui.rs/recipes/apps/spawn-vim/), [Ratatui `Terminal` docs](https://docs.rs/ratatui/latest/ratatui/struct.Terminal.html).

Do not use `?` on Vim’s result before re-entry. Record both results first:

```rust
let vim: Result<std::process::ExitStatus, std::io::Error> =
    Command::new("vim").arg(path).status();

let reenter: Result<(), std::io::Error> = enter_tui_and_clear(&mut terminal);

match (vim, reenter) {
    (Ok(status), Ok(())) => /* now apply policy for status.success() */,
    (Ok(status), Err(tty)) => Err(HandoffError::Reentry { status, tty }),
    (Err(vim), Ok(())) => Err(HandoffError::Vim { vim }),
    (Err(vim), Err(tty)) => Err(HandoffError::Both { vim, tty }),
}
```

A nonzero Vim exit is an `Ok(ExitStatus)`; only decide it is an application failure *after* restoration succeeds. If re-entry fails, keep the reader stopped and report both the Vim outcome and the terminal error.

Handle SIGTERM outside the Crossterm event task, at the top-level supervisor:

```rust
let mut sigterm = tokio::signal::unix::signal(
    tokio::signal::unix::SignalKind::terminate()
)?;

tokio::select! {
    _ = sigterm.recv() => shutdown.cancel(),
    // normal app completion...
}
```

Have the sole terminal coordinator observe that cancellation token and run the same orderly shutdown/handoff cleanup. If Vim is running, explicitly signal/wait for that child (or its process group, if that is your policy); a SIGTERM sent to the parent is not implicitly a reliable child-shutdown mechanism. Tokio signal registration replaces the default signal disposition, so receiving SIGTERM must actually drive your shutdown path. [Tokio Unix signals](https://docs.rs/tokio/latest/tokio/signal/unix/struct.Signal.html).

`SIGKILL` (`kill -9`) is the hard-termination path that cannot run cleanup—no Rust drops, panic hook, async task, or terminal restoration code can execute.
