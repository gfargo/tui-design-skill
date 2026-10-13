**Short answer: no, not as you describe it.** You can share a policy and a set of tests, but each framework needs its own small adapter. The handler you described has three problems:

1. **Ctrl+Z and the external editor are not exits.** They hand the terminal over and take it back later. If they go through the "final exit" API, your app quits when the user only wanted to suspend or edit.
2. **In raw mode, Ctrl+C and Ctrl+Z don't create signals.** Raw mode turns off `ISIG`, so they arrive as the bytes `0x03` and `0x1A`, which show up as key events. Your SIGINT handler only runs for an external `kill -INT`. Editor handoff involves no signal at all.
3. **"Immediately restore raw mode" from inside the handler races the renderer.** The handler can run while a frame is half written, and the terminal gets a broken escape sequence. In Rust it's also unsafe, because a real signal handler may only call async-signal-safe functions. The handler should set a flag or send a message. The framework's own loop should do the restore.

## Common policy for all four

**Three separate lifecycles. Never merge them:**

| Trigger | Lifecycle | Result |
|---|---|---|
| Ctrl+C key, SIGINT, SIGTERM, SIGHUP | **Terminate** | Graceful exit through the framework, with a time limit |
| Ctrl+Z key, SIGTSTP | **Suspend** | Release the terminal, stop the process, take the terminal back on SIGCONT |
| "Open in $EDITOR" | **Handoff** | Release the terminal, run the child in the foreground, take the terminal back |

**Rules:**
- **Signal handlers only signal.** They set a flag or post a message, nothing else. All terminal I/O happens on the UI loop.
- **One owner releases the terminal, and releasing twice is harmless.** Release in this order:
  1. Stop the input reader.
  2. Stop rendering.
  3. Show the cursor.
  4. Turn off mouse, bracketed paste, focus reporting and keyboard-enhancement modes.
  5. Leave the alternate screen.
  6. Restore the saved termios.
  7. Flush.

  Taking the terminal back is the same list in reverse.
- **Release on every exit path:** normal quit, signal, panic or uncaught exception. Never call `os.Exit`, `std::process::exit`, `sys.exit` or `process.exit` before releasing. Those calls skip deferred cleanup and `Drop`.
- **Put a time limit on shutdown.** Supervisors like systemd and Kubernetes send SIGTERM, wait a grace period, then send SIGKILL. A second SIGINT or SIGTERM during shutdown means: release the terminal, then exit at once.
- **Report the signal to the parent.** Exit with 128+N (130 for SIGINT, 143 for SIGTERM). Better still, reset the signal to its default and re-raise it, so the shell sees a "killed by signal" status.
- **SIGHUP means the terminal is gone.** Don't write to it, because writes can fail with EIO or SIGPIPE. Save state and exit.
- **Platform limits:** Windows has no SIGTSTP or SIGCONT and only a weak form of SIGTERM. Disable suspend there instead of faking it.

## Framework-specific exceptions

**Bubble Tea**
- The framework already handles SIGINT and SIGTERM. Don't add your own `signal.Notify` unless you also pass `tea.WithoutSignalHandler()`. If you do, your handler should only call `p.Quit()` or `p.Send(...)`. Use `p.Kill()` as the forced fallback.
- Ctrl+C arrives as a key message. Return `tea.Quit` from `Update`.
- For Ctrl+Z, return `tea.Suspend`. The framework releases the terminal, sends SIGTSTP, takes the terminal back, and delivers `tea.ResumeMsg`.
- For the editor, use `tea.ExecProcess(cmd, callback)`. It stops the input reader, which matters: otherwise your reader steals the editor's keystrokes. It then releases the terminal and repaints when the editor exits.
- These APIs moved around between v1 and v2. Check the version you're on.

**Ratatui**
- There is no runtime, so you write every part of this yourself.
- Use `ratatui::init()` / `ratatui::restore()` (`init` also installs a panic hook that restores the terminal), or call crossterm directly.
- For SIGTERM and SIGINT, use a `signal-hook` flag or `tokio::signal::unix`. Check it in the event loop with a poll timeout, then break out and restore on the normal path.
- **Ctrl+Z (you implement it):**
  1. Call `restore()`.
  2. Raise SIGTSTP with the default action. If you registered your own SIGTSTP handler, use `signal_hook::low_level::emulate_default_handler`.
  3. When execution continues, call `init()` again.
  4. Call `terminal.clear()`. Without this the diff renderer still trusts its old buffer and only redraws what changed.
- **Editor:** first stop or park any background event-reading thread. Then `restore()`, `Command::new(editor).status()`, `init()`, `terminal.clear()`.

**Textual**
- Exit with `App.exit(return_code=...)`.
- Ctrl+C is not quit in recent versions: Ctrl+Q quits and Ctrl+C copies. Decide deliberately whether to keep that.
- For SIGTERM, register `loop.add_signal_handler(SIGTERM, self.exit)`. That callback runs on the event loop, so calling `exit` from it is safe. Check first that your Textual version doesn't already install a handler.
- For Ctrl+Z, use the built-in `action_suspend_process`. It works only on Unix; on Windows and textual-web it raises `SuspendNotSupported`.
- For the editor: `with self.suspend(): subprocess.run([editor, path])`. Textual takes the terminal back and redraws on exit from the `with` block. You still have to reload your own data.

**Ink**
- `exitOnCtrlC` (on by default) handles the key. Exit through `useApp().exit()` or `instance.unmount()`, and wait on `waitUntilExit()`.
- **SIGTERM catch:** adding a `process.on('SIGTERM')` listener turns off Node's default "terminate" behaviour. Call `unmount()`, then add a timeout that calls `process.exit(143)`. Otherwise open handles can keep the process alive.
- Ctrl+Z has no built-in support. You implement it:
  1. `setRawMode(false)`, and leave the alternate screen if you entered it.
  2. `process.kill(process.pid, 'SIGTSTP')`. Don't add a SIGTSTP listener, or the default "stop" action is lost.
  3. On `SIGCONT`: `setRawMode(true)`, then `instance.clear()`, then re-render.
- **Editor:**
  1. `setRawMode(false)` and pause stdin.
  2. Run the editor with `spawnSync` (or `spawn` and await it) using `stdio: 'inherit'`.
  3. Turn raw mode back on and resume stdin.
  4. Call `clear()` and re-render. Ink's log-update counts the lines of the previous frame, and that count is wrong after the editor has used the screen.

## What to refresh after the editor returns (and after SIGCONT)

1. **Terminal modes:** raw termios, alternate screen, hidden cursor, mouse, bracketed paste, focus events and keyboard-enhancement flags. The editor may have changed or reset any of them.
2. **Size:** read the window size again. A resize may have happened while you were away, and the SIGWINCH may have gone to the child.
3. **Full repaint:** throw away diff buffers and previous-frame state. Don't trust the old screen.
4. **Stale input:** discard bytes typed or sent during the handoff (`tcflush(TCIFLUSH)` or the equivalent).
5. **App data:** reload the edited file (compare mtime or a hash), check the editor's exit status, and handle "not saved" and "file deleted".
6. **Time-based state:** tickers, spinners, "last updated" labels and polling intervals. After SIGCONT the gap can be hours long.
7. **Optional:** anything you detected by querying the terminal, such as background colour or theme, if the user may have changed it.

## SIGKILL (and SIGSTOP)

- **SIGKILL cannot be caught, blocked or handled. No cleanup runs:** no defers, no `Drop`, no `finally`, no exit hooks. The terminal stays raw, possibly on the alternate screen, with mouse reporting on and the cursor hidden.
  - Some shells restore termios when a foreground job dies, but terminal modes such as the alternate screen and mouse reporting usually stay on.
  - The user's way out is `reset` or `stty sane` followed by `tput rmcup`.
- **Design for it, don't try to handle it:**
  - Write persistent state atomically (write a temp file, then rename).
  - On startup, clean up stale lock, PID and temp files.
  - Keep SIGTERM shutdown well inside the supervisor's grace period.
  - If a guaranteed restore matters, a small parent wrapper process can restore the terminal after the child dies.
- **SIGSTOP** is the uncatchable version of Ctrl+Z. The process freezes without releasing the terminal, which stays raw until SIGCONT. Your SIGCONT path should therefore take the terminal back and repaint even if your own suspend code never ran.

**What to share across the four codebases:** this policy, a common list of terminal modes to turn on and off, and one integration-test script that checks terminal state after each scenario: `kill -TERM`, `kill -INT`, Ctrl+Z then `fg`, the editor round-trip, a resize while in the editor, and `kill -KILL`. The adapters themselves should stay framework-native.
