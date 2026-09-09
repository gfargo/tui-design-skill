No—share a **policy and adapter interface**, not one literal “restore raw mode then exit” handler. Ctrl+Z, an external editor, and termination are different lifecycle transitions.

| Event | Safe common action |
|---|---|
| Ctrl+C / `SIGINT` | Deliver an *interrupt/cancel* intent to the app; quit only if your app policy chooses it. |
| `SIGTERM` | Queue one graceful shutdown on the framework’s event loop, then let its normal finalization restore the terminal. |
| Ctrl+Z / `SIGTSTP` | **Temporarily release** the terminal, suspend the process, then reacquire it on `SIGCONT`; do not exit. |
| External editor/pager | **Temporarily release** terminal ownership, wait for the child, then restore/repaint; do not exit. |
| `SIGKILL` | No cleanup path exists. |

The shared contract should be: signal reception only sets/enqueues a lifecycle request; framework-owned code performs terminal I/O and final exit. Restoration is more than raw mode: it may include cursor visibility, alternate screen, mouse/focus reporting, bracketed paste, keyboard protocols, buffered output, and input-reader ownership. Keep the transition idempotent (`Running → Exiting` only once) and never let a child-editor handoff race with shutdown.

Do not call framework APIs from a low-level asynchronous POSIX signal handler. Schedule work onto Go’s goroutine/event loop, Rust async loop, Python asyncio loop, or Node event loop. Python explicitly permits event-loop interaction from `loop.add_signal_handler`, unlike a direct signal handler; Node listeners replace Node’s default `SIGINT`/`SIGTERM` exit behavior. [Python asyncio](https://docs.python.org/3/library/asyncio-eventloop.html#unix-signals), [Node signals](https://nodejs.org/api/process.html#signal-events)

Framework-specific exceptions:

- **Bubble Tea:** normally leave its signal handling enabled. It maps `SIGINT` to `InterruptMsg` and `SIGTERM` to `QuitMsg`; handle `InterruptMsg` in the model if interrupt means cancel rather than exit. Use `tea.Quit` inside `Update` or `Program.Quit()` externally. For an editor use `tea.ExecProcess` (preferred), or the matched `ReleaseTerminal()` / `RestoreTerminal()` pair—not final quit. Bubble Tea’s restore reinitializes input and repaints; its suspend path emits `ResumeMsg`. [signal behavior](https://github.com/charmbracelet/bubbletea/blob/main/tea.go), [Bubble Tea lifecycle APIs](https://pkg.go.dev/github.com/charmbracelet/bubbletea)

- **Ratatui:** Ratatui is rendering-focused; your app owns the signal/event loop. Prefer `ratatui::run` for normal final cleanup, or ensure `ratatui::restore()` executes on every cooperative exit if using `init()`. For suspend/editor, explicitly leave alt screen, disable raw mode and app-enabled protocols, then re-enter them on return; Ratatui’s own recipe does exactly that for `SIGTSTP`. [init/restore](https://docs.rs/ratatui/latest/ratatui/init/), [suspend recipe](https://ratatui.rs/recipes/apps/terminal-and-event-handler/)

- **Textual:** use `self.exit()` only for actual final app exit. Use `with self.suspend():` around an editor; it stops app I/O and returns the terminal to its pre-app configuration, then resumes afterward. Ctrl+Z is disabled by default; bind `ctrl+z` to `suspend_process` only on Unix. It is unsupported/no-op in Textual Web and Windows. [Textual suspension](https://textual.textualize.io/guide/app/#suspending), [API](https://textual.textualize.io/api/app/)

- **Ink:** use `useApp().exit()` / the render instance’s unmount path for final exit, not `process.exit()` from your handler. Ink’s `exitOnCtrlC` defaults to true specifically because raw mode prevents terminal Ctrl+C from generating `SIGINT`. For an editor use `await suspendTerminal(callback)` (or resume it in `finally`); Ink restores modes and forces a full redraw. If you add `process.on("SIGINT" | "SIGTERM")`, you now own exit completion because Node removes its default behavior. [Ink lifecycle and suspension](https://www.npmjs.com/package/ink), [Node signal semantics](https://nodejs.org/api/process.html#signal-events)

After an editor returns—or after foreground resume—ensure these are refreshed:

- Reacquire all TUI modes and restart/resume the input reader.
- Re-read terminal size and invalidate layout.
- Force a full redraw; do not trust a diff renderer’s previous screen cache.
- Re-enable every optional protocol your dashboard uses (mouse, paste, focus, keyboard enhancements) and restore cursor state.
- Reload/reconcile the edited file and any external data that changed while detached; resume timers/subscriptions and clear stale queued input/render work.

Finally, `SIGKILL` is deliberately uncatchable, unblockable, and unignorable, so neither raw mode nor any framework cleanup can run. Design for it as a failure case: rely on the terminal emulator/shell where possible, avoid irreversible in-memory-only work, and offer `stty sane` as operator recovery if a terminal is left malformed. [signal(7)](https://man7.org/linux/man-pages/man7/signal.7.html)
