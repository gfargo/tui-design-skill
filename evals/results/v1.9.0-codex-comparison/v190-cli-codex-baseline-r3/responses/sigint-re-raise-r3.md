`os.Exit(130)` exits normally with status 130. It does **not** terminate the process with SIGINT.

Although shells commonly display SIGINT termination as `128 + 2 = 130`, the underlying wait status distinguishes:

- Normal exit with code 130.
- Termination by signal 2 (SIGINT).

Shells such as Bash use that distinction when deciding whether Ctrl+C should also interrupt a loop running a foreground command. By catching SIGINT and exiting normally, your CLI can make the shell treat the interrupt as handled and continue the loop.

After cleanup, restore the default signal behavior and send SIGINT to yourself:

```go
// After receiving SIGINT and completing cleanup:
signal.Reset(os.Interrupt)
if err := syscall.Kill(os.Getpid(), syscall.SIGINT); err != nil {
    // Handle the failure.
}
```

Let the signal terminate the process; don’t immediately follow this with `os.Exit(130)`, which could race with signal delivery. This example is for Unix systems.