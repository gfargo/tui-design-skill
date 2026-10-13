**No.** A shared handler that restores raw mode and calls the final exit API gets three things wrong:

1. **Ctrl+Z and Ctrl+C aren't signals in raw mode.** All four frameworks turn off the terminal's signal generation, so these arrive as keypresses. A SIGINT handler never sees Ctrl+C from the keyboard; it only sees `kill -INT` from outside.
2. **An editor and a suspend are temporary handoffs.** If you call the final exit API, the app is torn down and can't come back. Each framework has its own API for lending the terminal and taking it back.
3. **Restoring the terminal inside a signal handler competes with the framework.** The renderer may be halfway through a frame, and the framework's own cleanup then runs a second time. Bubble Tea, `ratatui::run`/`init`, Textual's `App.run()` and Ink all already own cleanup.

## Safe common policy

What you can share is a policy, not a handler:

- **Signals only ask for shutdown.** SIGINT or SIGTERM sets a shutdown request or sends a quit event into the event loop. The handler never touches the terminal itself.
- **One shutdown path.** The loop exits through the framework's normal path, which restores the terminal. The process sets its exit status only after that returns. Common values are 130 for SIGINT, 143 for SIGTERM, 0 for a deliberate quit.
- **Make it idempotent.** Register handlers once at the process boundary and treat a repeated request as a no-op. Optionally, a second signal can force an exit after a timeout. That forced path is the only place for manual best-effort restore, done as separate steps: leave raw mode, leave the alternate screen, turn off mouse and paste modes, show the cursor.
- **Handoffs never call the final exit API.** Use each framework's handoff API: pause input → restore the shell-facing terminal → run and wait → re-enter → reload data → full redraw.
- **Ctrl+Z is a key binding** that calls the framework's suspend. Suspend is Unix-only, so offer another path on Windows (e.g. hide the binding or open a shell instead).

## Framework-specific exceptions

| | SIGINT/SIGTERM | Ctrl+C key | Editor | Ctrl+Z |
|---|---|---|---|---|
| **Bubble Tea v2** | **Don't add a handler.** The default one already converts external SIGINT/SIGTERM into a managed shutdown. Don't use `defer p.RestoreTerminal()` as cleanup; it re-enters Bubble Tea's modes rather than restoring the shell's. | `tea.KeyPressMsg` → `tea.Interrupt` (caller gets `ErrInterrupted`) or `tea.Quit`. Never call `os.Exit` in `Update`. | `tea.ExecProcess(cmd, cb)`, then reload in the callback message. | `tea.Suspend`, then reload on `tea.ResumeMsg`. |
| **Ratatui 0.30** | **You own this.** Ratatui doesn't turn signals into events. Use tokio's or another signal integration to send a quit event into the loop, then let `ratatui::run` restore. Default SIGTERM doesn't unwind Rust code, so `Drop`-based cleanup won't run. | Your own key handling sends quit. | Stop the input reader first (otherwise it steals the editor's keystrokes) → `ratatui::restore()` → run the editor → re-enable raw mode and the alternate screen → `terminal.clear()` → restart input → reload → draw. Keep both the editor's error and the re-entry error; `?` would drop one. | Same handoff. Send SIGTSTP only after restoring; re-initialize after SIGCONT. |
| **Textual 8** | Textual doesn't map SIGTERM to `App.exit`. If you need it, have the event loop schedule `self.exit(...)` (e.g. `loop.add_signal_handler` on Unix). Never restore the terminal in a low-level handler. Then `sys.exit(app.return_code)` after `run()`. | Binding → `self.exit(...)`. | `with self.suspend():` around an argv-based subprocess. Handle `SuspendNotSupported` (Textual Web can't hand over a terminal). | `suspend_process`, plus `app_resume_signal` for reloading. Does nothing on Windows and Textual Web. |
| **Ink 7.1+** | `exitOnCtrlC` only handles the keypress; it doesn't catch OS signals. For signals: register once, `unmount()`, `await waitUntilExit()`, set `process.exitCode`, remove the listeners. No `process.exit()` before output flushes. | `exitOnCtrlC` or `useApp().exit()`. | `await suspendTerminal(async () => runEditor())` (not available in Ink 6 or 7.0). Don't unmount. Keep one owner, because overlapping suspensions throw. | No built-in API. Send SIGTSTP inside `suspendTerminal`; it re-enters and redraws when the job resumes. |

## What to refresh after an editor returns

The framework handles the terminal side: re-entering modes and the full redraw. What it can't do is refresh your data. **A redraw only repaints the old model.** You own:

- **Data the editor could have changed:** the edited file, config, and anything derived from it. Re-read it and re-validate it.
- **Data that went stale while you were away:** pollers and live streams were paused. Refresh now, or mark panels stale until fresh data arrives, and reconnect any dropped connections.
- **Timers and tickers** you paused yourself. Ratatui doesn't pause them for you.
- **Size:** the terminal may have been resized during the handoff, so lay out again from the current size, not the cached one.
- **Selection and focus:** if reloaded rows disappeared, clamp the cursor to what remains.
- **The editor's result:** show a non-zero exit or a failed re-entry. Don't swallow it.
- **Ratatui only:** restart the input reader and re-enter the modes yourself.

## What SIGKILL means

SIGKILL can't be caught, and no cleanup runs in any of the four. The terminal stays in raw mode on the alternate screen with the cursor hidden. The user has to recover with `reset` or `stty sane; tput rmcup`. So:

- Make SIGTERM shut down quickly and reliably, so supervisors (systemd, Docker, k8s) finish within the grace period before they escalate to SIGKILL.
- Don't rely on exit-time cleanup for anything durable. Write files atomically (temp file + rename), make locks and pidfiles stale-detectable, and expect orphaned child processes.
- A crash, out-of-memory kill or power loss behaves the same way. Panic hooks cover panics, not these.

## Test it

In one PTY smoke test per framework, check:

- **External signals:** `kill -INT` and `kill -TERM` produce the correct exit status and leave the terminal clean.
- **Ctrl+C keypress:** exits cleanly with the correct status.
- **Editor round trip:** the dashboard shows the edited data afterward, not just a repaint.
- **Ctrl+Z then `fg`:** works on Unix.
- **Resize during the handoff:** the layout is correct on return.

Run the state-reload logic as unit tests without a terminal.
