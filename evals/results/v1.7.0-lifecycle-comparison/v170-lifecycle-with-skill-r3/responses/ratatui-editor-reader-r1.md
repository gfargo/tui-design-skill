Give the terminal to Vim exclusively:

1. Cancel the Crossterm reader task **and await its exit** (don’t merely drop its channel).
2. Restore the TUI terminal state: leave alternate screen, disable raw mode, restore cursor/mouse/paste modes as applicable.
3. Spawn Vim and wait for its status.
4. Regardless of Vim’s outcome, reclaim the terminal: re-enter the TUI modes, clear, then force a full draw.
5. Restart the input-reader task only after re-entry succeeds.

This prevents the reader from stealing Vim’s terminal capability replies (notably background-color responses), which otherwise arrive as garbage events and corrupt the next frame. Ratatui’s external-editor recipe calls out this exact failure mode. [Ratatui: Spawn External Editor](https://ratatui.rs/recipes/apps/spawn-vim/)

Do not use `?` between the child wait and re-entry: that loses Vim’s failure if re-entry also fails. Retain both results and aggregate them:

```rust
let vim = Command::new("vim").arg(path).status().await;
// `vim`: Err(spawn/wait failure), or Ok(status), including nonzero status.

let reenter = tui.enter()
    .and_then(|_| tui.terminal.clear())
    .and_then(|_| tui.terminal.draw(|f| app.draw(f)));

match (vim, reenter) {
    (Ok(status), Ok(())) if status.success() => Ok(()),
    (Ok(status), Ok(())) => Err(Error::VimExited(status)),
    (Err(vim_err), Ok(())) => Err(vim_err.into()),
    (Ok(_), Err(term_err)) => Err(term_err.into()),
    (Err(vim_err), Err(term_err)) => Err(Error::VimAndReentry {
        vim: vim_err.into(),
        reentry: term_err.into(),
    }),
}
```

For higher assurance, make re-entry itself best-effort and collect failures from each operation; setup/teardown helpers are not transactional.

`SIGTERM` should be converted by a Tokio Unix signal listener into a `Quit`/cancellation event for the app’s owning loop. The loop then returns normally through `ratatui::run(...)` (or your `init → run → restore` boundary), so cleanup runs. Do not call `process::exit()` from the signal task; it bypasses normal unwinding/cleanup.

`SIGKILL` (`kill -9`) is the hard-termination path that cannot run cleanup: it cannot be caught, deferred, or handled by panic hooks or `Drop`.
