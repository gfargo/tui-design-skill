# Exit code 130 isn't the same as being killed by SIGINT

Exit code 130 (128 + 2) is only a convention for showing that a process died from SIGINT. The shell doesn't look at that number. It calls `wait()` and checks `WIFSIGNALED(status)`. If your process calls `os.Exit(130)`, the status is "exited normally with code 130", not "terminated by signal 2".

When you press Ctrl+C, the terminal sends SIGINT to the whole foreground process group, so the shell sees it too. Bash then waits for the child and decides what to do based on how it ended (this is called "wait and cooperative exit"):

- **Child was killed by SIGINT:** the user wanted to stop everything, so bash stops the loop or script.
- **Child exited normally:** bash assumes the child handled Ctrl+C itself, like `vim` or `less` do, and the loop keeps going.

Your CLI handles SIGINT and then exits normally, so the shell treats Ctrl+C as handled and continues the loop.

## Fix: after cleanup, re-raise the signal with its default action

```go
sigCh := make(chan os.Signal, 1)
signal.Notify(sigCh, os.Interrupt)

go func() {
	sig := <-sigCh
	cleanup()

	// Restore default disposition and re-raise so the parent sees
	// WIFSIGNALED/WTERMSIG == SIGINT, not a normal exit.
	signal.Reset(sig)
	syscall.Kill(syscall.Getpid(), sig.(syscall.Signal))

	// Signal delivery is async; don't fall through to a normal exit.
	select {}
}()
```

**Why this works:** once you call `signal.Reset`, the Go runtime handles SIGINT itself again. Its default action resets the handler to the OS default and raises the signal again, so the process really does die from SIGINT. The shell sees a signal death and stops the loop, and `$?` still shows 130.

## Things to watch for

- **Exit by signal on every path.** If your main goroutine also handles cancellation, for example through `signal.NotifyContext`, it can return from `main` or call `os.Exit` before the re-raise happens. Every Ctrl+C path should end with the re-raise, not `os.Exit(130)`.
- **Don't exit by signal if you handled Ctrl+C as normal input.** An example is an interactive prompt that cancels the current input and keeps running. In that case a normal exit is the right behavior.
- **Windows** has no equivalent. Keep `os.Exit(130)` behind a build tag (`//go:build windows`) and use the re-raise everywhere else.

## How to check the fix

```sh
while true; do ./yourcli; done   # Ctrl+C should now break out
```

Under bash, you can also run `./yourcli; echo $?` and press Ctrl+C. You'll get 130 either way, but only the re-raise version will stop the loop.
