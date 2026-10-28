`os.Exit(130)` reports a **normal exit with code 130**, not termination by SIGINT. The shell can distinguish them even though both commonly appear as `$? = 130`.

Bash uses that distinction when deciding whether to abort a loop after Ctrl+C. Your CLI catches the signal and exits normally, so Bash can treat the interrupt as handled and continue.

On Unix, finish cleanup, restore default SIGINT handling, then signal yourself:

```go
// After cleanup has completed:
signal.Reset(os.Interrupt)
if err := syscall.Kill(syscall.Getpid(), syscall.SIGINT); err != nil {
    os.Exit(130) // fallback if sending the signal fails
}
select {} // delivery is asynchronous; wait for signal termination
```

Use imports `os`, `os/signal`, and `syscall`. Don’t immediately call `os.Exit(130)` after `Kill`: it can race with signal delivery.

Bound cleanup with a timeout, and let a second Ctrl+C force termination. Also remember that `os.Exit` skips deferred functions, so cleanup must finish before this termination path.

Verify the fix by checking that the subprocess’s Unix wait status reports `Signaled()` and `Signal() == syscall.SIGINT`; checking only `$?` won’t catch this bug.