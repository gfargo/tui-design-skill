`os.Exit(130)` is a **normal exit with code 130**, not termination by `SIGINT`. Although shells commonly display both as `$? = 130`, their underlying wait statuses differ.

When Ctrl+C reaches a foreground command, the shell may wait for that command’s result to decide whether to interrupt the loop. Your program catches the signal and exits normally, so the shell may continue looping.

After cleanup, restore the default signal behavior and send `SIGINT` to yourself:

```go
// After receiving SIGINT and completing cleanup:
signal.Reset(os.Interrupt)

if err := syscall.Kill(os.Getpid(), syscall.SIGINT); err != nil {
    os.Exit(130) // Fallback if signaling fails.
}

// Signal delivery is asynchronous; don't exit normally first.
select {}
```

This is Unix-specific. The key is to **terminate by the signal**, rather than merely return the exit code conventionally associated with it.