No. Share a **lifecycle policy**, not one handler that restores raw mode and final-exits for every case.

| Event | Common policy | Result |
|---|---|---|
| Ctrl+C / SIGINT, SIGTERM | Request one final shutdown through the framework/event loop; let its managed teardown run once. | App ends |
| External editor / shell | Temporarily hand the terminal to the child, then resume the same app. | App continues |
| Ctrl+Z / SIGTSTP | Restore terminal first, suspend, then re-enter and redraw on SIGCONT. | App continues |
| SIGKILL | No handler or cleanup runs. | Abrupt termination |

A process signal callback should only record/cancel/schedule “shutdown requested.” Don’t directly toggle raw mode or invoke UI APIs there: it can race the renderer/input reader, is not uniformly signal-safe, and may cause the framework to reacquire the terminal after you restored it. Have the owning UI loop perform orderly final exit; make that path idempotent. A second signal may escalate to immediate termination, with the known risk of a damaged terminal.

Framework specifics:

- **Bubble Tea v2:** do not add a competing SIGINT/SIGTERM handler in the normal case. Ctrl+C in raw mode is a `tea.KeyPressMsg`; return `tea.Interrupt` or `tea.Quit` by your exit-code policy. Bubble Tea’s handler also turns external SIGINT/SIGTERM into managed termination. Use `tea.ExecProcess` for an editor and `tea.Suspend` for Ctrl+Z; handle `tea.ResumeMsg`. `ReleaseTerminal`/`RestoreTerminal` are a temporary pair, not final cleanup. [Bubble Tea signal handling](https://github.com/charmbracelet/bubbletea/blob/main/tea.go), [editor handoff](https://github.com/charmbracelet/bubbletea/blob/main/exec.go)

- **Ratatui:** it owns rendering/setup, not your signal loop. Translate SIGTERM into a quit/cancellation event, return from `ratatui::run(...)` (or restore after your `run` result), and let that boundary clean up. For an editor, stop the input-reader task, leave alt screen/disable raw mode, wait for the child, reinitialize, clear, and fully redraw. For Ctrl+Z, do that handoff *before* SIGTSTP and reinitialize after SIGCONT. [Ratatui’s editor recipe](https://ratatui.rs/recipes/apps/spawn-vim/)

- **Textual:** call `self.exit(...)` only for final exit. Use `with self.suspend(): subprocess.run(...)` for an editor. Ctrl+Z is opt-in via `suspend_process`, Unix-only; it is ignored on Windows and Textual Web. Schedule `self.exit` from the app/event loop for SIGTERM—don’t manipulate the driver in a low-level signal callback. [Textual app lifecycle and suspension](https://textual.textualize.io/guide/app/)

- **Ink:** `exitOnCtrlC` handles Ctrl+C input bytes, **not SIGTERM**. At the render boundary, a SIGTERM listener should `unmount()`, await `waitUntilExit()`, then set the process status; don’t call `process.exit()` before the flush. Use `await suspendTerminal(async () => runEditor())` for editors; do not unmount. Ctrl+Z needs a Unix-only implementation inside that suspension. [Ink suspension and shutdown API](https://github.com/vadimdemedes/ink)

After an editor or resume, refresh two things:

1. **Terminal ownership/state:** resume input, raw mode, alt screen, cursor, paste/mouse modes; re-measure size, discard or pause stale input-reader events, clear if required, and force a full redraw.
2. **Application state:** reread the edited file/buffer, invalidate caches, re-stat/re-query resources the child could have changed, and preserve selection by stable IDs where possible. A redraw only repaints the old model; it does not reload data.

`SIGKILL` cannot be caught, deferred, awaited, or cleaned up. No framework exit API, `finally`, panic hook, or `atexit` handler runs. Termios/raw-mode state can therefore remain broken; recovery may require `stty sane` or `reset` from a usable shell. Design supervisors to send SIGTERM with a grace period before SIGKILL, and treat SIGKILL/OOM termination as unrecoverable.
