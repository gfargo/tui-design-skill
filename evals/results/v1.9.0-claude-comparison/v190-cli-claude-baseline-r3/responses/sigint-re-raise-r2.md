# The problem: exiting with 130 isn't the same as being killed by SIGINT

The shell can tell the difference between these two cases:

- **`exit(130)`**: the process exited normally (`WIFEXITED`) with status 130.
- **Killed by SIGINT**: the process was terminated by a signal (`WIFSIGNALED`, `WTERMSIG == SIGINT`). The shell shows this as `$? == 130`, but the kernel reports it differently.

When you press Ctrl+C, the terminal sends SIGINT to the whole foreground process group, so the shell sees it too. Bash, zsh and others use **"wait and cooperative exit"**: they wait for the child, then check how it ended.

- If the child **died from SIGINT**, the shell treats the Ctrl+C as meant for everything and stops the loop or script.
- If the child **exited normally**, even with 130, the shell assumes the child handled Ctrl+C on purpose. Programs like `vim` or `less` use Ctrl+C internally. So the shell keeps the loop running.

Your CLI handles the signal and then exits normally, which tells the shell "I dealt with it, carry on."

# The fix: clean up, then re-raise the signal

After cleanup, restore the default SIGINT behavior and send SIGINT to your own process so it actually dies from the signal:

```go
sigCh := make(chan os.Signal, 1)
signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)

go func() {
    sig := <-sigCh
    cleanup()

    // Restore default disposition and re-raise so the parent sees
    // WIFSIGNALED rather than a normal exit.
    signal.Reset(sig)
    if s, ok := sig.(syscall.Signal); ok {
        _ = syscall.Kill(syscall.Getpid(), s)
    }

    // Fallback in case the signal didn't kill us (e.g., it was ignored).
    os.Exit(128 + int(sig.(syscall.Signal)))
}()
```

This works in Go because once `signal.Reset` runs, the runtime handles SIGINT/SIGTERM with `dieFromSignal`. That sets the handler back to `SIG_DFL` and raises the signal again, so the process really is killed by it.

# Notes

- **Windows:** `syscall.Kill` doesn't exist there, so put the re-raise in a `//go:build unix` file and just `os.Exit(130)` on Windows.
- **The fallback `os.Exit` is still needed.** If SIGINT was ignored when the program started (for example, it was started with `nohup` or in the background by a non-interactive shell), Go keeps it ignored and the self-kill does nothing.
- **Use `context` cancellation if you have it.** If you're using `signal.NotifyContext`, let `main` return normally after cleanup and do the reset and re-raise at the end of `main`. Don't call `os.Exit` from a goroutine partway through work.
- **Checking the fix:** `for i in 1 2 3; do ./yourcli; done` and press Ctrl+C. The loop should stop at once. `$?` will still show 130, but now it comes from the signal.

This is the same rule described in "Proper handling of SIGINT/SIGQUIT" (Bernhard Schmidt's WCE write-up), and it's the reason well-behaved tools re-raise the signal instead of calling `exit(130)`.
