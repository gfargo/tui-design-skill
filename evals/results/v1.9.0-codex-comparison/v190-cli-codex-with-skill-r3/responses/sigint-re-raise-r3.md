`os.Exit(130)` reports a **normal exit with code 130**, which differs from **termination by SIGINT**. Both can appear as `$? = 130`, but the shell can distinguish them.

Shells such as Bash use that distinction when deciding whether Ctrl+C should abort a loop. Your handler makes the interrupt look handled, so the loop can continue.

On POSIX, clean up, restore SIGINT’s default behavior, then send SIGINT to your own process:

```go
// After bounded cleanup and terminal restoration:
signal.Reset(os.Interrupt)
if err := syscall.Kill(syscall.Getpid(), syscall.SIGINT); err != nil {
    os.Exit(130) // fallback if sending the signal fails
}

// Signal delivery is asynchronous; don't return from main or call os.Exit.
select {}
```

This uses `os`, `os/signal`, and `syscall`; keep it in platform-specific code for Unix systems.

Also let a second Ctrl+C force termination during cleanup. To verify the fix, check that the child’s wait status indicates **SIGINT termination**, rather than checking only `$?`.