No—share a lifecycle policy, not one “restore raw mode + final-exit” handler.

| Event | Common policy |
|---|---|
| Ctrl+C / `SIGINT`, external `SIGTERM` | Request a one-time **final exit through the framework/event loop**; let its normal teardown restore the terminal. Don’t call `exit(…)`, unmount, or raw-mode APIs directly from a low-level signal handler, and don’t call `process.exit()`/`os.Exit()`. |
| Ctrl+Z / `SIGTSTP` | **Temporary handoff**, not exit: release terminal → suspend → on `SIGCONT`, reacquire terminal, clear/full-redraw, reload mutable state. |
| External editor/shell | Same temporary-handoff boundary. Use the framework’s editor/terminal-suspension API; never final-exit the app. |
| `SIGKILL` | No cleanup runs—no handler, `finally`, `defer`, panic hook, or framework API. Raw mode/alt screen/cursor state may remain damaged; recovery is `stty sane` or `reset`. |

A reusable abstraction can emit intents such as `FinalExit(cause)`, `Handoff(editor)`, `Suspend`, and `Resume`. Each implementation maps those to its native APIs. Keep terminal ownership framework-specific.

| Framework | Final exit | Editor / Ctrl+Z exception |
|---|---|---|
| Bubble Tea v2 | `tea.Quit`, or `tea.Interrupt` when the caller needs interruption status. Bubble Tea manages normal signal termination; don’t add raw-terminal cleanup around `Program.Run()`. | Use `tea.ExecProcess` for editors; it releases and restores the terminal. Use `tea.Suspend`, then handle `tea.ResumeMsg`. [Bubble Tea exec lifecycle](https://github.com/charmbracelet/bubbletea/blob/v2.0.8/exec.go) |
| Ratatui | Ratatui does not own signal policy. Send a quit/cancel event into your loop and return through `ratatui::run(...)` (or `restore()` in a `finally`-equivalent). | Stop the input-reader task, leave alt screen/disable raw, run editor, reinitialize, clear, full redraw. Suspend similarly around `SIGTSTP`/`SIGCONT`. [Official editor recipe](https://ratatui.rs/recipes/apps/spawn-vim/) |
| Textual | Schedule `self.exit(...)` on its event loop; don’t manipulate raw mode in a signal handler. | Use `with self.suspend():` for an editor. Bind `ctrl+z` to `suspend_process` on Unix; it is intentionally unavailable on Windows and Textual Web. [Textual suspend docs](https://textual.textualize.io/guide/app/#suspending-the-application) |
| Ink 7 | For OS `SIGTERM`, have a boundary listener call `unmount()`, then await `waitUntilExit()`; `exitOnCtrlC` only handles Ctrl+C input bytes in raw mode. | Use `await suspendTerminal(async () => runEditor())`. For Unix Ctrl+Z, suspend inside that handoff and resume/redraw afterward; don’t unmount. [Ink lifecycle](https://github.com/vadimdemedes/ink/blob/v7.1.1/readme.md#app-lifecycle), [terminal suspension](https://github.com/vadimdemedes/ink/blob/v7.1.1/readme.md#suspendterminalcallback) |

After an editor or resume, refresh more than pixels:

- Re-read files/config/data the external program or shell may have changed; a redraw alone preserves stale in-memory state.
- Reacquire raw mode, alternate screen, cursor/mouse/input modes; clear and force a full draw at the current terminal size.
- Restart/pause-resume input readers as needed—especially Ratatui/Crossterm, so editor terminal responses are not consumed by your app.
- Revalidate selection/focus against reloaded data and surface child-process or re-entry errors separately.

The important distinction: **shutdown destroys the session; suspend/editor lends it out.** Treating all three as final exit is what breaks resume.
