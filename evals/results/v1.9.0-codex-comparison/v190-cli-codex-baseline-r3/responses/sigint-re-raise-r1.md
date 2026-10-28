`os.Exit(130)` is a **normal exit with status 130**, not termination by SIGINT. The convention `128 + signal number` doesn’t make the two equivalent.

Shells such as Bash distinguish them. When handling Ctrl+C during a loop, Bash checks whether the foreground command actually died from SIGINT. A normal exit of 130 can let the loop continue.

After cleanup, restore SIGINT’s default behavior and signal yourself again. On Unix:

```go
cleanup()

signal.Reset(os.Interrupt)
if err := syscall.Kill(syscall.Getpid(), syscall.SIGINT); err != nil {
    os.Exit(130) // fallback
}
select {} // wait for signal termination
```

This preserves the signal termination status the shell needs to recognize the interrupt.