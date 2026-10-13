**No, don't share one handler.** It merges three different boundaries, and it does the wrong thing on two of them:

1. **Final exit cannot resume.** If you call the framework's final exit API on Ctrl+Z or when opening an editor, the dashboard ends when the user expected it to pause.
2. **Restoring raw mode from a signal handler races the renderer.** The renderer may still be writing frames and the input reader may still be consuming bytes. In Python, Rust and Node, that kind of terminal I/O doesn't belong inside a low-level handler anyway.
3. **Ctrl+C and Ctrl+Z usually aren't signals.** In raw mode they arrive as ordinary key events. Your SIGINT handler only sees an *external* `kill -INT`, and no SIGTSTP is generated unless the app sends one itself.

Share a **policy spec and a test matrix**. Implement it with each framework's own lifecycle API.

## The common policy

| Boundary | Common rule |
|---|---|
| **Ctrl+C key** | Treat it as an app action (quit, or cancel the current operation). Go through the framework's normal exit path, then exit with status 130. |
| **External SIGINT / SIGTERM** | Turn the signal into a quit message inside the event loop. Never touch the terminal in the handler. Let the framework's run or unmount path restore the terminal. Exit 130 or 143. Put a time limit on cleanup, and make a second signal force-exit. |
| **Ctrl+Z (Unix only)** | Hand the terminal back to the shell temporarily: pause input, restore the shell's terminal settings, send SIGTSTP. After SIGCONT, switch the terminal modes back on, reload data, and do a full redraw. Never call final exit. On Windows, hide this action or offer a different one, because Windows has no SIGTSTP or SIGCONT. |
| **External editor** | Use the same temporary handoff: stop the input reader *first*, restore, run the editor and wait for it, re-enter, reload, full redraw. Keep the editor's exit status. If both the editor and re-entry fail, report both errors. |
| **Panic / uncaught error** | Use the framework's own restore-on-crash (in Rust, a panic hook) or its finally/cleanup path. Install your error-reporting hooks *before* the framework's, so the terminal is restored before the report prints. |
| **Who owns it** | One owner per process. Components and widgets never switch raw mode or the alternate screen themselves, and never call `exit` directly. |

## Framework-specific exceptions

**Bubble Tea v2**: the framework already owns all of this.
- Its default signal handler already turns SIGINT/SIGTERM into a clean shutdown. **Don't add your own.**
- Ctrl+C arrives as a key press. Return `tea.Interrupt` (the caller gets `tea.ErrInterrupted`) or `tea.Quit`.
- Ctrl+Z: return `tea.Suspend`, then reload in the `tea.ResumeMsg` handler.
- Editor: `tea.ExecProcess(exec.Command(...), cb)` handles release, wait, restore and repaint. Reload in the callback message.
- Don't `defer p.RestoreTerminal()` as final cleanup. It *re-enters* Bubble Tea's terminal modes; it doesn't restore the shell. Never call `os.Exit` from `Update`.

**Ratatui 0.30**: Ratatui owns terminal setup, but not your event loop or signals.
- Use `signal-hook` or `tokio::signal` to send a quit event into the loop. The closure then returns through `ratatui::run(...)`, or through `init()` → loop → `restore()` with the result kept.
- Default SIGTERM does **not** unwind Rust, so no `Drop` cleanup runs unless you handle the signal.
- Ctrl+Z has no built-in support. Cancel and await the input-reader task, call `ratatui::restore()`, send SIGTSTP to yourself, then after SIGCONT re-enable raw mode and the alternate screen and call `terminal.clear()`.
- Editor: follow Ratatui's official external-editor recipe ("spawn vim"). A reader left running steals the editor's keystrokes and terminal responses.

**Textual**
- Desktop drivers have no general mapping from SIGTERM to `App.exit`. Use event-loop integration (for example, asyncio's `loop.add_signal_handler`) to *schedule* `app.exit(return_code=143)`. Then call `sys.exit(app.return_code)` after `app.run()`, because `return_code` is only metadata otherwise.
- Ctrl+Z: bind `suspend_process`. It does nothing on Windows and Textual Web. Reload by subscribing to `app_resume_signal`.
- Editor: run the editor inside `with self.suspend():`, passing the command as an argument list. Handle `SuspendNotSupported` (Textual Web) with a non-terminal alternative.
- `suspend()` (lend the terminal) and `suspend_process` (Unix job control) are different APIs. Neither one is final exit.

**Ink**
- `exitOnCtrlC` only handles the Ctrl+C keypress. It is **not** a SIGTERM handler.
- Register `process.once('SIGTERM'/'SIGINT')` once, where you call `render()`. In the handler: `unmount()`, `await waitUntilExit()`, set `process.exitCode`, remove the listeners. Never call `process.exit()` before that finishes flushing.
- Editor: `await suspendTerminal(async () => runEditor())`, available in Ink 7.1+ (not in 7.0 or 6). Don't unmount.
- Ctrl+Z: Ink has no built-in job-control action. If you need it, send SIGTSTP *inside* `suspendTerminal`.
- Only one suspension may be active at a time; a second overlapping one throws. Keep a single place in the app that suspends.

## What to refresh after an editor (or Ctrl+Z) returns

A redraw only repaints the old model. It does not refresh any data. After you get control back:

1. **Re-read anything the editor could have changed.** Read the file from disk again, then re-parse and re-validate it. If the edit is invalid, show an error state rather than keeping stale values silently.
2. **Re-query the terminal size and lay out again.** The user may have resized the window while away, and you missed that resize event.
3. **Refresh live dashboard data.** Polls and ticks stopped while you were paused. Mark panels as stale (e.g. "updated 4m ago"), then fetch now rather than waiting for the next tick. Reconnect streams that timed out.
4. **Restart the input reader** (Ratatui; Ink and Textual do this themselves) and make sure focus and selection still point at rows that exist.
5. **Do a full redraw.** Bubble Tea's ExecProcess, Ink's `suspendTerminal` and Textual's `suspend()` do this for you; Ratatui needs `terminal.clear()` before the next draw.
6. **Show the editor's result.** A non-zero exit status or a re-entry error should appear in the UI, not disappear.

## What SIGKILL means

SIGKILL can't be caught, blocked or handled. **No cleanup runs**: no handler, no `finally`, no `Drop`, no `defer`, no panic hook. The terminal stays in raw mode on the alternate screen with the cursor hidden, plus any mouse or bracketed-paste modes you enabled. The parent shell sees exit status 137. The user has to recover with `reset` or `stty sane`; your app can't fix this.

What this means for the design:
- **Make saved data crash-safe.** Write to a temp file and rename it into place, so correctness never depends on cleanup having run. Clean up leftover temp and lock files on the *next* startup.
- **An unhandled SIGTERM is just as bad for the terminal.** By default in Rust, Python and Node, SIGTERM kills the process with no cleanup, the same as SIGKILL. That's why each port needs its own SIGTERM-to-quit path, except Bubble Tea, which already has one.

**Shared test matrix for all four ports** (run as one or two pseudo-terminal end-to-end tests each): `q`, Ctrl+C, external `kill -INT`, `kill -TERM`, a double signal, a panic or exception, an editor round trip that changes the file, and Ctrl+Z → `fg` on Unix. After each, assert the shell's terminal settings (`stty -g`) match the pre-launch snapshot and the exit codes are 0, 130 and 143.
