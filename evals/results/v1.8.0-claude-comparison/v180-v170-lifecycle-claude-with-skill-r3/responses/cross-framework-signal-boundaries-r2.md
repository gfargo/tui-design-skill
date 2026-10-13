**No, don't share one handler like that.** The idea breaks in four places:

1. **Ctrl+C and Ctrl+Z don't arrive as signals in a full-screen app.** Raw mode delivers them as keypresses. No SIGINT or SIGTSTP is generated unless the app sends one itself, so a signal handler never sees them.
2. **Calling the final exit API ends the app for good.** An editor handoff or a suspend has to come back to a live UI. Bubble Tea, Textual, and Ink each have a separate handoff API for this. Ratatui doesn't, so you write the handoff yourself.
3. **Restoring the terminal inside a signal handler races the render loop.** A frame can be half-written when the handler runs, or the loop can redraw after you restore. Textual's guidance says this directly: don't restore the terminal from a low-level signal handler.
4. **Bubble Tea already handles SIGINT and SIGTERM.** A second handler would compete with it.

What you can share is a **policy**: a small set of named intents that each implementation maps to its framework's API.

## The shared policy

| Boundary | What triggers it | Common rule |
|---|---|---|
| **Final shutdown** | Quit key, Ctrl+C key, SIGINT/SIGTERM from outside, fatal error | The signal handler only sends a "quit requested" event into the event loop. The loop returns through the framework's managed cleanup. Make it idempotent so a second signal doesn't run cleanup twice. Exit with 130 for SIGINT, 143 for SIGTERM, and 0 for an intentional quit. Never call `os.Exit`, `process.exit()`, or `sys.exit` from inside the loop. |
| **Temporary handoff** (editor, shell) | User action | Use the framework's handoff API: stop input, give the terminal back to the shell, run the child and wait, re-enter, refresh (see below). Never unmount or quit. |
| **Job-control suspend** | Ctrl+Z **key** | Use the framework's suspend action on Unix. On Windows, offer a different action (for example "open shell") because SIGTSTP doesn't exist there. |
| **Panic or crash** | Bug | Rely on the framework's panic restoration. Ratatui wraps any reporting hook installed before `init()`, Bubble Tea recovers inside `Run()`, and Textual and Ink restore in their run/unmount paths. |

Keep logging out of the terminal throughout. While the UI owns the terminal, diagnostics go to a file.

## Framework-specific exceptions

**Bubble Tea v2**: register **no** signal handler; the default one turns external SIGINT/SIGTERM into managed termination.
- **Ctrl+C key:** return `tea.Interrupt` (the caller gets `tea.ErrInterrupted`) or `tea.Quit`.
- **Editor:** use `tea.ExecProcess(cmd, callback)`.
- **Ctrl+Z:** return `tea.Suspend`, then handle `tea.ResumeMsg`.
- **Don't use `defer p.RestoreTerminal()` as cleanup.** `ReleaseTerminal` and `RestoreTerminal` are a temporary handoff pair, and `RestoreTerminal` puts the terminal back into Bubble Tea's modes, not the shell's.

**Ratatui 0.30**: this is the one implementation that **needs** your signal integration, because Ratatui doesn't turn signals into events.
- **SIGINT/SIGTERM:** use `tokio::signal` or `signal-hook` to send a quit event into the loop. Let `ratatui::run(...)` (or your saved-result-then-`restore()` path) do the cleanup. Default SIGTERM doesn't unwind Rust, so destructors won't run unless you route the signal this way.
- **Editor:** do the handoff yourself, in this order:
  1. Stop and await the input reader first. Otherwise it steals the child's keystrokes.
  2. Call `ratatui::restore()`.
  3. Run the child and wait.
  4. Turn raw mode back on and re-enter the alternate screen.
  5. Re-enable any other modes you turned on at startup, such as mouse capture or keyboard enhancement flags.
  6. Call `terminal.clear()`.
  7. Start a new input reader.
  8. Reload data, then redraw.

  Re-entry isn't transactional. Keep the child's result, and if both the child and re-entry fail, report both errors.
- **Ctrl+Z:** do the same restore first, then send SIGTSTP, and do the re-entry steps after SIGCONT.

**Textual**: there's no general SIGTERM-to-`App.exit` path on desktop.
- **SIGTERM:** use the event loop's own signal integration to schedule `self.exit(return_code=...)`. Then call `sys.exit(app.return_code)` after `app.run()`, because `return_code` doesn't become the process status on its own.
- **Editor:** run it inside `with self.suspend():`. Handle `SuspendNotSupported`, which you'll get on Textual Web.
- **Ctrl+Z:** use `suspend_process`. It's a no-op on Windows and Textual Web. Subscribe to `app_resume_signal` to reload data when the app resumes.

**Ink**: `exitOnCtrlC` only handles the Ctrl+C keystroke in raw mode, not OS signals.
- **SIGINT/SIGTERM:** register the listeners **once** where you call `render()`. In the listener, call `unmount()`, `await waitUntilExit()`, set `process.exitCode`, and remove the listeners. Don't call `process.exit()` before the terminal writes finish.
- **Editor:** use `await suspendTerminal(async () => runChild())` (Ink 7.1 or later). Route all suspensions through one place, because starting a second one while the first is active is an error.
- **Ctrl+Z:** Ink has no built-in suspend action. Send SIGTSTP from inside `suspendTerminal` so its resume path re-enters and redraws.

## What to refresh after the editor returns

A full redraw only repaints the **old** model. After the handoff, refresh all of these:

- **Data:** reread any file, config, or VCS state the editor could have changed, and rerun anything derived from it (filters, sorting, counts).
- **Selection and scroll:** check them again, since the selected row may have moved or disappeared.
- **Size:** reread the terminal size, because the user may have resized during the edit.
- **Input and modes:** make sure input is running again and every terminal mode you rely on is back on. Ratatui needs this done by hand; the other three re-enter for you.
- **Child result:** show the editor's exit status. For example, a non-zero exit means the edit was aborted, so don't apply it.
- **Redraw:** force a full repaint. The handoff APIs do this; in Ratatui, call `clear()` before the next draw.

## What SIGKILL means

**There is no cleanup.** SIGKILL can't be caught, so no handler, `defer`, `Drop`, `finally`, or exit hook runs, and the terminal stays in raw mode on the alternate screen.

- The user's way out is to run `reset` or `stty sane`. Put this in your troubleshooting docs.
- Design for it: write persistent state atomically (write a temp file, then rename) or incrementally. Never rely on saving at exit.
- The other implementations aren't safe from crash-style exits either: default SIGTERM also skips Rust unwinding unless you route it through the loop as above.

## Tests to add to each implementation

Use one or two pseudo-terminal (PTY) smoke tests per implementation:

- **SIGTERM:** send `kill -TERM` and check that the terminal is restored and the exit status is 143.
- **Editor round trip:** use a fake `$EDITOR` that changes the file, then check that the UI shows the new data and the terminal modes are intact.
- **Ctrl+Z:** press Ctrl+Z, then `fg`, then check that the UI redraws and the data reloads (Unix only).
