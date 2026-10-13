**No.** A single handler that restores the terminal and calls the framework's final exit API will break two of your three cases. Ctrl+Z and opening an external editor are temporary: the app must give up the terminal and later take it back. Only shutdown should end the app. Each framework also has its own signal handling and render state, and a generic handler can fight with them.

What you can share is the **policy**: the order of steps, the list of terminal modes, and the exit codes. The handlers themselves should be written per framework.

## 1. Three separate lifecycles

| Trigger | Lifecycle | Ends the app? | Final exit API? |
|---|---|---|---|
| Ctrl+Z / SIGTSTP | **Suspend → resume** (SIGCONT) | No | **No** |
| External editor ($EDITOR) | **Release → reacquire** | No | **No** |
| SIGINT / SIGTERM / SIGHUP / quit key | **Shutdown** | Yes | Yes, once |

**Key presses are not signals while in raw mode.** Raw mode turns off `ISIG`, so pressing Ctrl+C or Ctrl+Z sends the app a key event, not SIGINT or SIGTSTP. A real SIGINT or SIGTSTP comes from outside, for example `kill`, a supervisor, or the shell. Each case therefore has two entry points (a key and a signal), and both should call the same internal routine.

## 2. Common policy for all four

**Signal handler rule:** the handler only *requests* a shutdown, for example by setting a flag, sending to a channel, or posting a message to the event loop. It never touches the terminal directly. If it restored the terminal right away, it would race the render loop, which can then draw one more frame into a terminal that is back in normal mode. Rust signal handlers also can't safely do terminal I/O at all.

**Teardown order** (the same for suspend, release and shutdown):
1. Stop the input reader so it doesn't steal keystrokes meant for the editor or shell.
2. Stop the renderer and flush any pending output.
3. Turn off the extra modes you turned on: mouse tracking, bracketed paste, focus reporting, and kitty keyboard flags (pop them).
4. Show the cursor and reset text attributes (SGR).
5. Leave the alternate screen.
6. Restore the **saved** terminal settings (termios) from startup. Don't just "disable raw mode" generically.

**Shutdown rules:**
- Run the cleanup only once, even if it's called several times.
- A second SIGINT during shutdown forces an immediate exit (after a best-effort terminal restore).
- Exit with `128 + signal number` (130 for SIGINT, 143 for SIGTERM). Alternatively, reset the signal to its default action and raise it again, so the parent process sees that you were killed by a signal.
- On SIGHUP the terminal may already be gone. Writes can fail with EIO, so skip the visual cleanup, save your state and exit.
- Finish shutdown within your supervisor's grace period before it sends SIGKILL. The defaults are 10s for Docker and 90s for systemd.

**Suspend rules:**
- Do the teardown.
- Set SIGTSTP back to its default action, then send SIGTSTP to the process group.
- When execution continues (after SIGCONT), re-install your handler and run the refresh checklist in section 4.

## 3. Framework-specific exceptions

Check these against the versions you've pinned, because the defaults have changed between releases.

**Bubble Tea (Go)**
- The program already handles SIGINT and SIGTERM by turning them into messages that end `Run()` and restore the terminal. **Don't add a second `signal.Notify` handler.** Either use its handling, or turn it off with `tea.WithoutSignalHandler()` and cancel through `tea.WithContext(ctx)`.
- Ctrl+C arrives as a `KeyMsg`. For a normal shutdown, return `tea.Quit`. `p.Kill()` skips the final render but still restores the terminal.
- For Ctrl+Z, return `tea.Suspend`. Handle `tea.ResumeMsg` to refresh your data.
- For the editor, use `tea.ExecProcess(cmd, callback)`. It releases and reacquires the terminal and pauses the input reader, and your callback receives the editor's exit error.
- Don't do this by hand with `os/exec` plus raw mode calls.

**Ratatui (Rust)**
- There is no runtime, so the app owns every step.
- `ratatui::init()` installs a panic hook that restores the terminal. Keep it, and call `ratatui::restore()` on every exit path.
- For signals, use `signal-hook` (an `AtomicBool` flag) or `tokio::signal`, and check it in the event loop.
- Ctrl+Z arrives as a crossterm `KeyEvent`. Tear down, then use `signal_hook::low_level::emulate_default_handler(SIGTSTP)` or `raise`, then set up again.
- **Call `terminal.clear()` after every resume or editor return.** Ratatui only redraws what changed since its last frame. Without the clear, it assumes the screen is still intact and draws only partial updates.
- Also turn off any crossterm modes you enabled yourself, such as `EnableMouseCapture` or `PushKeyboardEnhancementFlags`.

**Textual (Python)**
- For the editor, use `with self.suspend():` and run `subprocess.run([editor, path])` inside the block.
- For Ctrl+Z, use the built-in `action_suspend_process` (Unix only).
- Quit with `App.exit(return_code=...)`. Note that since Textual 1.0, Ctrl+C means copy and **Ctrl+Q** quits.
- I don't believe Textual handles SIGTERM. Python's default action for SIGTERM kills the process with no cleanup, leaving the terminal broken. Register one in `on_mount`: `asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, self.exit)`.
- Don't use a raw `signal.signal` handler that calls UI code.

**Ink (Node)**
- `exitOnCtrlC` defaults to true. The final exit API is `useApp().exit()` or `instance.unmount()`, followed by `await waitUntilExit()`.
- Ink registers an exit hook (via `signal-exit`), but **adding your own `process.on('SIGTERM')` listener turns off Node's default exit for that signal**. Your listener must then unmount and call `process.exit(143)` itself.
- `process.on('exit')` callbacks must be synchronous.
- There is no built-in suspend. Do it yourself:
  1. `stdin.setRawMode(false)` and `stdin.pause()`.
  2. `process.kill(process.pid, 'SIGTSTP')`.
  3. On `SIGCONT`: `setRawMode(true)`, `resume()`, `instance.clear()`, then force a re-render.
- For the editor: pause stdin and turn off raw mode first, or Ink's input listener will eat the editor's keystrokes. Then run `spawnSync(editor, [file], { stdio: 'inherit' })`, and restore raw mode and force a full repaint afterwards.
- Ink uses the main screen by default, so its diff-based output is easily corrupted by whatever the editor drew.

## 4. Refresh checklist after an editor returns (and after SIGCONT)

**Terminal state**
- Raw mode, alternate screen, hidden cursor, mouse, bracketed paste, focus reporting and kitty keyboard flags must all be re-applied. The editor or shell may have changed any of them.
- **Read the window size again.** The user may have resized the window while the editor was open, and you probably missed SIGWINCH.
- **Throw away the cached last frame and repaint everything.** That means `terminal.clear()` in Ratatui, `instance.clear()` plus a re-render in Ink; Bubble Tea and Textual repaint for you, so just confirm it happens.
- Drain or discard any stale buffered input.

**App state**
- Check the editor's exit status. A non-zero exit or an unchanged mtime means "cancelled".
- Re-read the edited file from disk. Don't trust what you held in memory.
- Refresh dashboard data that went stale during the pause. Ratatui with a blocking spawn and Ink with `spawnSync` both freeze their event loops, so timers and polls didn't run.
- Restart or re-sync tickers instead of letting them catch up all at once.

## 5. What SIGKILL means for cleanup

SIGKILL (and SIGSTOP) can't be caught, so **no cleanup runs**: no handler, no `defer`/`Drop`/`finally`, no exit hook.

**The terminal stays broken.** The kernel closes your file descriptors, but the terminal's settings belong to the terminal device, not your process. The user is left with raw mode, the alternate screen, a hidden cursor and possibly mouse reporting still on. Some shells (zsh, fish) partly reset this at the prompt; bash mostly doesn't. The user recovers with `reset` or `stty sane; tput rmcup; tput cnorm`.

**How to design for it:**
- Never rely on cleanup for data correctness. Write files atomically (write to a temp file, then rename), and use lock files that check whether the recorded PID is still alive.
- If you need guaranteed terminal recovery, use a small parent wrapper. It saves the settings with `stty -g`, runs the TUI as a child, and restores the settings after the child exits. Only a different process can clean up after SIGKILL.
- Keep SIGTERM shutdown fast so supervisors never need to escalate to SIGKILL.

**Recommendation:** put the policy in one shared spec: the teardown order, the list of terminal modes, the refresh checklist and the exit codes. In each implementation, write a small adapter with three hooks (`release()`, `reacquire()`, `shutdown(code)`) built on that framework's own APIs. Then test each one the same way:
- `kill -TERM`
- `kill -INT`
- `kill -TSTP` followed by `fg`
- resizing the window while the editor is open
- `kill -9` followed by checking `stty -a`
