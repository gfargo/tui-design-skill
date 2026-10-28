The problem is that exiting with code 130 isn't the same as dying from SIGINT, and the shell can tell the difference.

## Why the loop keeps going

When you press Ctrl+C, the terminal sends SIGINT to the whole foreground process group. That includes your program and the bash running the loop. Bash then waits for your program to finish and checks **how** it ended:

- **The child was killed by SIGINT** (`WIFSIGNALED`, signal 2): bash takes this to mean the user wants to stop, so it aborts the loop or script.
- **The child exited normally, even with code 130**: bash takes this to mean the child handled the Ctrl+C itself (the way an editor or a REPL does), so it continues with the next iteration.

`os.Exit(130)` is a normal exit. The 128+N convention is only how the shell *reports* death-by-signal in `$?`. Returning 130 yourself doesn't make you look signal-killed. This is the "wait and cooperative exit" behavior described in [Cracauer's write-up](https://www.cons.org/cracauer/sigint.html).

## The fix: re-raise the signal after cleanup

After cleanup, restore the default SIGINT behavior and send the signal to your own process. The kernel then kills the process and bash sees a real signal death.

```go
sigs := make(chan os.Signal, 1)
signal.Notify(sigs, os.Interrupt)

go func() {
    <-sigs
    fmt.Fprintln(os.Stderr, "\nInterrupted, cleaning up…")

    // A second Ctrl+C during cleanup forces an immediate exit.
    go func() {
        <-sigs
        os.Exit(130)
    }()

    // Put a time limit on cleanup so it can't hang.
    done := make(chan struct{})
    go func() { cleanup(); close(done) }()
    select {
    case <-done:
    case <-time.After(5 * time.Second):
    }

    // Restore default disposition and die by SIGINT.
    signal.Reset(os.Interrupt)
    syscall.Kill(syscall.Getpid(), syscall.SIGINT)

    // Delivery is asynchronous, so wait briefly.
    // If somehow still alive, fall back to exit code 130.
    time.Sleep(time.Second)
    os.Exit(130)
}()
```

Notes:

- **`signal.Reset` is required.** Without it, Go's handler catches your own re-raised signal and puts it back on the channel.
- **The `os.Exit(130)` at the end is only a fallback.** Normally the process dies before it gets there. A second Ctrl+C also still ends the process, though only with code 130.
- **`syscall.Kill` is POSIX-only.** On Windows this situation doesn't come up, so put the re-raise behind a build tag and keep `os.Exit(130)` there.
- **If you don't need cleanup, don't call `signal.Notify` for SIGINT.** Go's default behavior already dies by signal correctly.

## Checking the fix

```sh
for i in 1 2 3; do ./yourcli long-task; echo "after $i"; done
```

Press Ctrl+C during the first iteration. Before the fix you'll see `after 1` and the loop moves to iteration 2. After the fix the loop stops, and `$?` still shows 130 because bash reports the signal death that way.
