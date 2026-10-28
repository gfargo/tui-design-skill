`os.Exit(130)` loses the fact that your process **was terminated by SIGINT**.

On Unix, these produce different wait statuses:

- `os.Exit(130)`: exited normally with code 130.
- Default SIGINT termination: killed by signal 2.

Both commonly appear as `$? = 130`, but shells such as Bash inspect the distinction. While waiting for a foreground command, Bash can interpret a normal exit as “the child handled the interrupt” and continue the loop.

After cleanup, restore default handling and send SIGINT to yourself:

```go
// Unix only; after receiving SIGINT:
cleanup() // Run explicitly; os.Exit does not run deferred functions.

signal.Reset(os.Interrupt)
if err := syscall.Kill(syscall.Getpid(), syscall.SIGINT); err != nil {
    os.Exit(130) // Fallback if signaling fails.
}

// Signal delivery is asynchronous. Don't return or call os.Exit yet.
select {}
```

Use imports `os`, `os/signal`, and `syscall`. Keep cleanup bounded, and restore default SIGINT handling before cleanup if a second Ctrl+C should terminate immediately.

To verify the fix, inspect the child’s `syscall.WaitStatus`: `Signaled()` should be true and `Signal()` should equal `syscall.SIGINT`. Checking only `$?` cannot distinguish the two cases.