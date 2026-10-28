Exiting with code 130 only imitates death by signal. The shell can tell the difference, and that's why the loop keeps going.

## Why it happens

When a child process exits, the shell gets a wait status from `waitpid()`. That status records one of two things:

- **The process exited normally** (`WIFEXITED`) with some code, such as 130.
- **The process was killed by a signal** (`WIFSIGNALED`), such as SIGINT.

`$?` shows 130 in both cases, but they are different states. Bash and most other shells use an approach called "wait and cooperative exit." When you press Ctrl+C, the terminal sends SIGINT to the whole foreground process group, so the shell sees it too. The shell then waits for the child and checks how it ended:

- **The child was killed by SIGINT:** the user wanted to stop everything, so the shell aborts the loop or script.
- **The child exited normally, even with 130:** the shell assumes the child handled SIGINT on purpose. Programs like `vim` or `less` do this. So the shell continues with the next iteration.

Your program handles the signal and then calls `os.Exit(130)`, so it lands in the second case.

## The fix

After cleanup, restore the default SIGINT behavior and send the signal to your own process. Then you actually die from SIGINT:

```go
sigCh := make(chan os.Signal, 1)
signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)

go func() {
	sig := <-sigCh
	cleanup()

	// Re-raise so the parent sees WIFSIGNALED, not a plain exit code.
	signal.Reset(sig)
	if s, ok := sig.(syscall.Signal); ok {
		_ = syscall.Kill(os.Getpid(), s)
	}
	// Fallback if the signal didn't terminate us for some reason.
	os.Exit(128 + int(sig.(syscall.Signal)))
}()
```

Notes:
- `signal.Reset` puts back the default action for that signal, which is to terminate. Calling `signal.Stop(sigCh)` also works.
- Keep the `os.Exit` fallback. Delivery is asynchronous, so the process might still be running for a moment after `Kill`. It also covers Windows, where `syscall.Kill` doesn't exist. Guard this code with a build tag if you build for Windows.
- Re-raise SIGTERM the same way, for the same reason.

## How to verify

```sh
for i in 1 2 3; do ./mycli; echo "iteration $i done"; done
```

Press Ctrl+C during the first run. With the fix, the loop stops and nothing is printed. Without the fix, `iteration 1 done` prints and the second run starts.

The standard write-up on this is Martin Cracauer's "Proper handling of SIGINT/SIGQUIT" (cons.org/cracauer/sigint.html).
