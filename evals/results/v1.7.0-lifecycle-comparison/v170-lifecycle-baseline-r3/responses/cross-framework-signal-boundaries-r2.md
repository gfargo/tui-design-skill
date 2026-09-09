No. Share a **lifecycle policy**, not one handler that directly manipulates terminal state.

A real signal handler must be minimal; terminal/framework calls can reenter renderers, locks, runtimes, or I/O. POSIX permits only a narrow set of async-signal-safe calls there. Notify the framework’s normal event loop, then let its exit/suspend API own teardown. [signal-safety(7)](https://man7.org/linux/man-pages/man7/signal-safety.7.html)

| Event | Common policy |
|---|---|
| Ctrl+C / SIGINT | Request framework-owned graceful exit/interrupt. In raw mode Ctrl+C is often an input byte, not SIGINT. |
| SIGTERM | Request one idempotent graceful shutdown; stop new work, let the framework restore its terminal state, then exit. |
| Ctrl+Z / SIGTSTP | **Suspend, don’t exit**: relinquish terminal, stop the process, reinitialize and fully redraw on resume. |
| External editor/pager | **Temporarily suspend**, wait for child, then restore/re-enter and redraw. Never use final-exit API. |
| SIGKILL | No cleanup is possible. |

Make the shared adapter expose `request_shutdown`, `suspend_for_child`, and `resume`; guard each with state/idempotence and keep signal reception separate from execution. A second termination request may be escalated by your supervisor after a short grace period, but don’t race two cleanup paths.

Framework-specific exceptions:

- **Bubble Tea:** usually install no duplicate SIGINT/SIGTERM handler: it already maps SIGINT to `InterruptMsg` and SIGTERM to `QuitMsg`. For Ctrl+Z, return `tea.Suspend()`; it releases the terminal, stops the process, restores the program on `fg`, and emits `ResumeMsg`. Use `ReleaseTerminal`/`RestoreTerminal` only for temporary handoff, not final shutdown. `Program.Kill()` is the emergency fast exit—it restores terminal state but skips the final render. [Bubble Tea signal handling](https://github.com/charmbracelet/bubbletea/blob/main/tea.go), [suspend implementation](https://github.com/charmbracelet/bubbletea/blob/main/tty.go), [API](https://pkg.go.dev/github.com/charmbracelet/bubbletea/v2)

- **Ratatui:** Ratatui does not own this as one global lifecycle; your TUI wrapper must. Its recommended pattern exits raw/alternate/mouse/paste modes, raises `SIGTSTP`, then re-enters on resume. Ensure cleanup also stops the event task before restoring the terminal. [Ratatui recipe](https://ratatui.rs/recipes/apps/terminal-and-event-handler/)

- **Textual:** use `with self.suspend(): run_editor()` for editors. Ctrl+Z is deliberately disabled by default; opt in by binding `ctrl+z` to `suspend_process`. Don’t replace it with `exit()`. Suspension is unavailable in Textual Web. [Textual suspension guide](https://textual.textualize.io/guide/app/)

- **Ink:** use `suspendTerminal()` for editors/pagers and `useApp().exit()` / the render instance’s normal unmount path for final exit. `suspendTerminal()` already disables raw mode and UI modes, pauses I/O, then reapplies state and forces a full redraw—even if the child throws. Be careful adding Node SIGINT/SIGTERM listeners: adding one removes Node’s default termination behavior, so your listener must reliably drive Ink shutdown. [Ink API](https://github.com/vadimdemedes/ink), [Node signal behavior](https://nodejs.org/api/process.html)

After an editor or `fg` returns, always:

- restart/re-arm input/event reading;
- re-query terminal dimensions (a resize may have occurred);
- re-enable exactly the UI-owned modes: raw, alternate screen, cursor policy, mouse, bracketed paste, enhanced/kitty keyboard, focus;
- invalidate prior frame/cursor assumptions and force a full redraw;
- reload the edited file/data and reconcile any background output that was paused.

`SIGKILL` cannot be caught, blocked, or ignored, so neither raw-mode restoration nor “final exit” runs. A supervisor should send SIGTERM first and reserve SIGKILL for a timeout. If SIGKILL leaves a terminal malformed, recovery is outside the process—typically `stty sane` and/or `reset`. [signal(7)](https://man7.org/linux/man-pages/man7/signal.7.html)
