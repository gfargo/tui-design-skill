No—share a lifecycle policy and adapters, not one “restore raw mode + exit” handler. Ctrl+Z, an editor handoff, and termination are different transitions.

| Event | Correct action |
|---|---|
| Ctrl+C / external `SIGINT`, `SIGTERM` | Queue one orderly shutdown on the framework’s event loop; let its final teardown restore the terminal. |
| Ctrl+Z / `SIGTSTP` | Release the terminal, then suspend; on `SIGCONT`, reacquire it and repaint. Do not exit. |
| External editor/pager | Temporarily release the terminal; restore and redraw afterward. Do not exit. |
| `SIGKILL` | No handler or cleanup can run. |

The portable policy:

- Have exactly one terminal owner and an idempotent state machine: `running → handing-off/suspended → running`, or `running → exiting → exited`.
- Treat raw-mode Ctrl+C/Ctrl+Z as *key events*, not necessarily signals: raw mode normally disables the terminal’s signal generation. In cooked mode Ctrl+Z is `SIGTSTP`, never `SIGINT`/`SIGTERM`.
- A signal callback should only request cancellation / enqueue an app event. Don’t call renderer, React, Python UI, or Ratatui terminal APIs from a low-level POSIX signal handler; run finalization on the framework/runtime loop.
- On termination, use the framework’s normal final-exit path once. It must restore more than raw mode: cursor visibility, alternate screen, mouse/focus/paste/keyboard modes, and input readers.
- While a child editor owns the terminal, suppress or scope the parent’s shutdown handling correctly: terminal-generated Ctrl+C is delivered to the foreground process group, so it may be intended for the editor rather than the dashboard.

Framework-specific adapters:

- **Bubble Tea:** avoid a competing global handler; Bubble Tea already maps `SIGINT` to `InterruptMsg` and `SIGTERM` to `QuitMsg`. Decide in `Update` whether `InterruptMsg` means `tea.Quit` or an interrupted return. Map Ctrl+Z to `tea.Suspend()`—Bubble Tea releases/restores the terminal and emits `ResumeMsg`. Use `tea.ExecProcess` for `$EDITOR`; it pauses/releases and restores the program around the child. Bubble Tea explicitly notes raw-mode Ctrl+C/Ctrl+Z must be handled per program. [signal handling](https://github.com/charmbracelet/bubbletea/blob/main/tea.go), [suspend implementation](https://github.com/charmbracelet/bubbletea/blob/main/tty.go), [editor process API](https://github.com/charmbracelet/bubbletea/blob/main/exec.go)

- **Ratatui:** Ratatui is rendering, not an application runtime; there is no framework “final exit API.” Put `ratatui::restore()` (or your equivalent: disable raw, leave alternate screen, disable mouse, show cursor) in one RAII/session guard, and route signals to your event loop so the guard drops normally. For an editor, stop input tasks, leave alternate screen and raw mode, wait for the editor, then re-enter raw/alternate mode, clear, and draw. [Ratatui’s editor recipe](https://ratatui.rs/recipes/apps/spawn-vim/) also warns that an unpaused event reader can consume the editor’s input or terminal responses.

- **Textual:** use `App.exit()` only for final exit. Use `with self.suspend():` for editors, and bind `ctrl+z` to `suspend_process` if desired; it is disabled by default and deliberately a no-op on Windows and Textual Web. [Textual suspension and exit](https://textual.textualize.io/guide/app/)

- **Ink:** let `exitOnCtrlC` handle raw-mode Ctrl+C by default, or call `useApp().exit()` / returned-instance `unmount()` and await `waitUntilExit()` before ending Node. Do not call `process.exit()` first. Use `suspendTerminal()` for editors/pagers; it restores terminal modes and forces a full redraw on resume. Ink has no equivalent documented, portable Ctrl+Z job-control wrapper, so implement that only as a POSIX adapter with `SIGTSTP`/`SIGCONT`. [Ink lifecycle and suspension](https://github.com/vadimdemedes/ink)

After an editor returns, refresh:

1. Reload the edited data from disk.
2. Restart/resume input consumption; discard or safely parse queued terminal negotiation replies.
3. Re-query terminal size and recompute layout.
4. Invalidate the renderer/frame cache and force a full repaint; restore all modes before accepting input.

`SIGKILL` is the hard limit: it cannot be caught, blocked, or ignored, so no `finally`, destructor, `defer`, exit hook, or framework cleanup runs. The OS closes file descriptors, but terminal mode and screen state can remain corrupted because those are properties of the TTY. Use SIGTERM with a grace period in supervisors; after SIGKILL, recovery is user-side (`reset`/`stty sane`) or a terminal-session cleanup wrapper. [POSIX signal definition](https://pubs.opengroup.org/onlinepubs/7908799/xsh/signal.h.html)
