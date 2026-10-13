**Short answer: no, not as you've described it.** You can share a policy, but a generic handler that restores raw mode and then calls the final exit API is wrong for two of your three cases:

- **Ctrl+Z is suspend, not exit.** The process has to come back.
- **An external editor isn't a signal at all.** It's "lend the terminal to a child process, then take it back."
- **Restoring raw mode yourself, outside the framework's loop, races the renderer.** It can also fight the framework's own restore.

There's also a premise problem. In raw mode the terminal's signal generation (ISIG) is off. Ctrl+C and Ctrl+Z arrive as key bytes (`0x03`, `0x1a`), not as SIGINT/SIGTSTP. A real SIGINT only shows up from `kill -INT`, from a child running in cooked mode, or before raw mode is entered.

(Your working directory is empty, so this is general guidance, not a review of your code.)

---

## 1. Safe common policy

Share this as a written contract plus a test matrix, not as shared code. The four runtimes have different threading and signal models.

**P1. The framework owns the terminal.** Your signal code only *requests* shutdown, through the framework's channel. The framework does the restore. Raw signal-handler context is not async-signal-safe for terminal I/O or teardown.

**P2. Restore is idempotent and ordered.** Guard it with a once-flag. The order:
1. Stop the renderer and the input reader.
2. Disable the modes you enabled:
   - mouse `?1000/1002/1003/1006l`
   - bracketed paste `?2004l`
   - focus `?1004l`
   - kitty keyboard pop `CSI < u`
   - modifyOtherKeys, if used
3. Leave the alt screen (`?1049l`), show the cursor (`?25h`), reset the cursor shape.
4. Restore the termios state you saved at startup.
5. Flush output.

**P3. Signal semantics:**

| Signal | Action |
|---|---|
| SIGTERM / external SIGINT | Graceful quit via the framework's exit API, with a deadline (finish well inside Docker's 10s / k8s's 30s grace period). |
| SIGHUP | The terminal is gone. Skip most writes (they'll EIO or EPIPE), save state, exit. |
| Second SIGINT/SIGTERM | Do the minimal restore (P2), then hard exit. |
| SIGTSTP / Ctrl+Z key | Suspend (§2). Never exit. |
| SIGCONT | Re-acquire (§3). |
| SIGTTOU/SIGTTIN | If you're resumed with `bg`, don't touch the terminal until `tcgetpgrp(fd) == getpgrp()`. |

**P4. Exit status should reflect the signal.** After cleanup, reset the disposition to default and re-raise, or exit with 128+signo (130 for INT, 143 for TERM). Shells and supervisors depend on this. Bash in particular uses it to decide whether to abort a script.

**P5. Ctrl+C is an app keybinding.** Decide per app whether it quits. Textual ≥1.0 binds Ctrl+Q to quit and uses Ctrl+C for copy, so the four frontends may intentionally differ.

**P6. Keep persistent state crash-safe on its own.** Write via temp file plus `rename`, and never depend on the exit path to make data consistent (see SIGKILL below).

## 2. Suspend (Ctrl+Z)

1. Release the terminal (P2, but keep the process alive).
2. Stop yourself: reset SIGTSTP to default and `raise(SIGTSTP)`, or `raise(SIGSTOP)`.
3. On SIGCONT, re-acquire (§3).

## 3. External editor: release, run, re-acquire

**Before spawning:**
- Release the terminal.
- **Stop your input reader.** This is the most common bug: a background stdin reader steals the editor's keystrokes.
- Ignore or defer SIGINT/SIGQUIT in the parent while the child runs, the same way `system()` does. A cooked-mode child shares your foreground process group, so a Ctrl+C meant for it would also hit you.

**After the editor returns (or after SIGCONT), refresh:**
- **termios:** re-apply your *known* raw config. Don't re-save whatever the editor left behind.
- **Modes:** re-enable alt screen, hidden cursor, mouse, bracketed paste, focus events, and the kitty keyboard flags.
- **Size:** query it again. SIGWINCH may have fired while you weren't listening.
- **Renderer:** invalidate the diff/back buffer, then clear and fully repaint. Every one of these frameworks diffs against what it thinks is on screen, and that is now wrong.
- **Input parser:** reset any half-parsed escape sequence state. Optionally drain stale input.
- **Cached terminal queries:** redo any you cached (background colour via OSC 11, capabilities), in case the user switched terminals or a multiplexer changed things.
- **App data:** reload the edited file and validate it. Recompute time-based state (ticks, "last updated" values) from the wall clock.
- **Signals:** restore the parent's SIGINT/SIGQUIT handlers.

## 4. Framework-specific exceptions

**Bubble Tea (Go)**
- The Program already handles SIGINT/SIGTERM, unless you used `WithoutSignalHandler`. From your own goroutine, call `p.Quit()` or `p.Kill()`. Don't restore the terminal yourself.
- Ctrl+Z arrives as a key message. Return `tea.Suspend`, and you'll get `tea.ResumeMsg` afterwards.
- For editors, use `tea.ExecProcess(cmd, cb)`. It stops the cancelable input reader and handles release and restore for you. Do your data reload in the callback message.
- Don't call `os.Exit` from a handler: deferred cleanup won't run.

**Ratatui (Rust)**
- There's no runtime, so you own the whole loop.
- Use `signal-hook` or `tokio::signal` only to set a flag or send on a channel. The loop then calls `ratatui::restore()`.
- Install a panic hook (`ratatui::init()` does this) and a Drop guard. `process::exit` skips Drop.
- Ctrl+Z is `KeyCode::Char('z')` with CONTROL. Restore, call `signal_hook::low_level::emulate_default_handler(SIGTSTP)`, then re-init on return.
- Editor flow: restore, then `Command::status()`, then re-init.
- After either one, call `terminal.clear()` to drop the diff buffer.
- If you read crossterm events on another thread or through `EventStream`, pause it first.

**Textual (Python)**
- Final exit is `app.exit()`. For SIGTERM, use `loop.add_signal_handler(SIGTERM, app.exit)`, or `app.call_from_thread` if you're off the loop thread.
- For editors, use `with self.suspend(): subprocess.run([...])`. It handles release, the input driver, and repaint. It raises `SuspendNotSupported` where suspending isn't possible (e.g. textual-serve/web).
- Ctrl+Z goes through the built-in `action_suspend_process` (Unix only).
- Reload app data on the `AppResume` signal or after the `with` block.

**Ink (Node)**
- It has no suspend or exec API, so this is where you write the most code yourself.
- Adding a `process.on('SIGINT')` listener removes Node's default exit. Have it call `instance.unmount()` (or `useApp().exit()`), then `await waitUntilExit()`, then re-raise or set the exit code.
- Set `exitOnCtrlC: false` if you want Ctrl+C to be a keybinding.
- **Ctrl+Z** (key with `key.ctrl` set):
  1. `stdin.setRawMode(false)`.
  2. Write out the mode-disable sequences, including leaving the alt screen if you entered one. Ink doesn't use the alt screen by default.
  3. `process.kill(process.pid, 'SIGSTOP')`.
  4. On `SIGCONT`: re-enable raw mode and the modes, then `instance.clear()` and `rerender()`. log-update's line count is stale.
- **Editor:** the same release steps, plus pause stdin. Then use `spawnSync(editor, args, {stdio: 'inherit'})` or await the child, and re-acquire.
- An app that won't exit after `unmount` has open handles (timers, sockets). Close them, or set a deadline and fall back to `process.exit`.

## 5. SIGKILL

SIGKILL (and SIGSTOP) can't be caught, blocked, or handled. **No cleanup runs.** No handlers, no defers, no Drop, no `finally`, no `exit` hooks. In practice:

- **The terminal stays broken:** raw mode, alt screen, mouse reporting, hidden cursor. The user has to run `reset`, or `stty sane; tput rmcup`.
  - The only real fix is **outside** the process: a tiny launcher that does `saved=$(stty -g)`, runs the TUI, then always runs `stty "$saved"` and writes the mode-off sequences.
  - That launcher is the one piece of cleanup code all four implementations can truly share.
- **Data:** anything not already atomically on disk is lost. That's why P6 matters.
- **Temp files** for editor buffers leak. Keep them in a known directory and sweep it at startup.
- **An editor child can be orphaned** and keep fighting over the TTY. It shares your process group, so a supervisor should kill the group, not just the PID.
- **Supervisors** (systemd, Docker, k8s) send SIGTERM and then SIGKILL after the grace period. Your graceful path has to finish inside it, or you'll hit all of the above.
