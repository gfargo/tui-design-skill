No—share a lifecycle policy, not one generic “restore raw mode + final-exit” signal handler. That conflates three distinct boundaries:

| Event | Correct operation |
|---|---|
| `SIGINT` / `SIGTERM` | Request final shutdown; let the framework’s normal exit path restore the terminal. |
| `Ctrl+Z` / `SIGTSTP` | Temporarily hand off the terminal, suspend, then re-enter and redraw on `SIGCONT`. Do **not** final-exit. |
| External editor | Temporarily hand off the terminal, wait for the child, then resume the same app. Do **not** final-exit. |

The safe common policy is:

1. Treat OS handlers as a shutdown *request*, not a place to manipulate raw mode or render state. Queue/cancel into the framework’s event loop; make shutdown idempotent.
2. Have the loop call its framework-native final-exit mechanism exactly once.
3. Model editor launch and job-control suspend as resumable terminal leases: stop UI input, restore shell-facing modes, perform the handoff, then reacquire terminal ownership.
4. On resume, force a full repaint **and reload externally mutable state**. A redraw restores pixels, not your dashboard model.
5. Keep `SIGKILL` outside the cleanup contract.

Framework adapters:

- **Bubble Tea:** Let `Program.Run()` own cleanup. In raw mode, Ctrl+C is normally a key message; use `tea.Quit` for a normal exit or `tea.Interrupt` when the caller should receive `ErrInterrupted`. Bubble Tea already manages external `SIGINT`/`SIGTERM`; don’t bolt on `os.Exit` or call `RestoreTerminal` as final cleanup. Use `tea.ExecProcess` for `$EDITOR`, and `tea.Suspend` for Ctrl+Z; reload on the editor callback and on `tea.ResumeMsg`. [`ExecProcess`](https://github.com/charmbracelet/bubbletea/blob/main/exec.go) releases and reacquires the terminal around the child, while Bubble Tea’s signal loop maps external termination into managed messages. [Bubble Tea signal source](https://github.com/charmbracelet/bubbletea/blob/main/tea.go)

- **Ratatui:** Ratatui does not own your general signal policy. Send a quit/cancellation event to your loop, let it return, then use `ratatui::run(...)` or the `init()` → result → `restore()` structure. For editor or Ctrl+Z: stop the input reader, leave alt-screen/disable raw mode, run or suspend, then reinitialize, clear, and redraw. This is necessarily more manual than the others. [Ratatui’s editor recipe](https://ratatui.rs/recipes/apps/spawn-vim/)

- **Textual:** Use `self.exit(...)` only for final app exit; schedule it through the asyncio/app lifecycle rather than restoring the terminal in a low-level signal handler. Use `with self.suspend():` for an editor, and `suspend_process` for Unix Ctrl+Z. These resume the app; they are not exit APIs. Textual Web and Windows need a non-job-control fallback. [Textual app lifecycle and suspension](https://textual.textualize.io/guide/app/)

- **Ink:** `exitOnCtrlC` handles raw Ctrl+C input; it is not a `SIGTERM` handler. At the render/process boundary, handle `SIGINT`/`SIGTERM` once, `unmount()`, await `waitUntilExit()`, then set the process status—never call `process.exit()` first. Use `await suspendTerminal(async () => runEditor())` for editors. Ink has no separate high-level Ctrl+Z API; if you support Unix job control, perform it inside `suspendTerminal`, not via unmounting. [Ink terminal suspension](https://github.com/vadimdemedes/ink/blob/v7.1.1/readme.md#suspendterminalcallback)

After an editor returns—or after `SIGCONT`—refresh:

- The edited file/config and its metadata.
- Any dashboard data the child could alter: processes, working directory, git state, caches, remote data.
- Selection validity, sort/filter results, and derived status.
- Current terminal dimensions/layout.
- The input reader if your framework/runtime paused it, then clear/full-redraw and restore cursor/mouse/keyboard modes.

Finally, **`SIGKILL` cannot be handled**. No `defer`, `finally`, Rust `Drop`, Node cleanup callback, framework exit API, or signal handler runs. Raw mode, alt-screen, cursor, or mouse state may remain stuck in the terminal. Use `SIGTERM` with a grace period first; `SIGKILL` is an emergency stop, not a clean exit.
