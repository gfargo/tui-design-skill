No. Share a **lifecycle policy**, not a generic handler that manipulates raw mode or calls a final-exit API.

`Ctrl+Z` and an external editor are *temporary handoffs*: the dashboard must resume. `SIGINT`/`SIGTERM` are *final shutdown requests*. A final exit/unmount for the former destroys the event loop or component tree you need to resume.

## Safe common policy

1. Have exactly one terminal-lifecycle owner: the framework.
2. Convert OS signals into an idempotent application event at the runtime/event-loop boundary; do not perform terminal I/O, rendering, or framework APIs inside a true low-level signal handler.
3. Handle three distinct intents:

| Intent | Terminal action | App action |
|---|---|---|
| Final shutdown | Framework cleanup once | End the run loop / unmount |
| Editor or shell | Temporarily yield terminal | Wait, then resume |
| Job-control suspend | Yield terminal, then suspend process | On `SIGCONT`, resume |

4. Treat a second termination request as escalation only after your documented grace period; never race multiple cleanup paths.
5. On all resumptions, force a full repaint **and reload/reconcile mutable domain state**.

`Ctrl+C` may be delivered as a raw input byte rather than OS `SIGINT`, so route it through each framework’s input model. `Ctrl+Z` likewise needs the framework’s job-control path; don’t bind it to “quit.”

## Framework-specific policy

| Framework | Final shutdown | Editor / temporary handoff | Ctrl+Z |
|---|---|---|---|
| Bubble Tea v2 | Return `tea.Quit` (or `tea.Interrupt` when caller needs `ErrInterrupted`). Its program lifecycle handles normal cleanup and its managed external-signal path. | `tea.ExecProcess(...)`; do not manually use final cleanup. | Return `tea.Suspend`; on `tea.ResumeMsg`, synchronize state. |
| Ratatui | Ratatui does **not** translate signals into events. Your signal integration sends quit/cancellation to the loop, which returns through `ratatui::run` or `restore`. | Pause the input reader, restore terminal, run editor, reinitialize, clear, redraw. | Same handoff sequence, then send `SIGTSTP`; reinitialize after `SIGCONT`. |
| Textual | Call `self.exit(...)` on the app/event loop. Schedule it from signal integration; don’t restore terminal state in a signal handler. | `with self.suspend(): run_editor()` | Bind/invoke `suspend_process`; unsupported/no-op on Windows and Textual Web. |
| Ink 7 | `exitOnCtrlC` handles Ctrl+C input only. For `SIGTERM`, register one process-boundary listener, `unmount()`, await `waitUntilExit()`, then set status. Do not call `process.exit()` first. | `await suspendTerminal(async () => runEditor())` | No high-level job-control API; on Unix, suspend within `suspendTerminal`, then resume through it. |

Bubble Tea’s `ExecProcess` deliberately pauses and resumes the program for interactive children; it is not equivalent to quitting. [Bubble Tea source](https://github.com/charmbracelet/bubbletea/blob/v2.0.8/exec.go)  
Ratatui’s editor recipe shows the required temporary leave-alt-screen/raw-off → child → restore sequence. [Ratatui recipe](https://ratatui.rs/recipes/apps/spawn-vim/)  
Textual provides separate APIs for editor suspension and foreground-process suspension. [Textual guide](https://textual.textualize.io/guide/app/#suspending-the-application)  
Ink’s suspension restores shell-facing modes and then performs a full redraw on resume. [Ink docs](https://github.com/vadimdemedes/ink/blob/v7.1.1/readme.md#suspendterminalcallback)

## Refresh after an editor returns

A redraw alone is insufficient. Refresh:

- The edited file’s content, metadata, parse/validation results, and dirty/conflict status.
- Filesystem, Git, config, task/process, or remote data the editor or shell could have changed.
- Derived lists, filters, counts, previews, and caches; preserve selection by stable ID, then clamp it if the item disappeared.
- Current terminal dimensions; invalidate layout and do a complete redraw.
- Ratatui specifically: ensure the old input-reader task is paused/stopped before re-entry, otherwise it can steal input.

The framework should restore raw mode, cursor, alternate screen, mouse/paste/input modes; your dashboard must restore **its model’s truth**.

## SIGKILL

`SIGKILL` cannot be caught, deferred, awaited, or cleaned up. No `defer`, `Drop`, `finally`, `atexit`, or framework exit path runs, so raw mode or the alternate screen may remain until the parent terminal/multiplexer recovers—or the user runs `stty sane` / `reset`.

For managed shutdown, send `SIGTERM`, allow a bounded grace period, then use `SIGKILL` only as forced termination. Never promise terminal cleanup after it.
