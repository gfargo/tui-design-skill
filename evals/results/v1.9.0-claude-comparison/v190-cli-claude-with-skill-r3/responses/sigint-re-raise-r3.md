Your tool exits with status 130 instead of dying from the signal. To the shell, those two look different.

## Why the loop keeps going

When you press Ctrl+C, the terminal sends SIGINT to the whole foreground process group, so bash gets it too. Bash then decides what to do based on how your child process ended. This is called "wait and cooperative exit" (see [Cracauer's write-up](https://www.cons.org/cracauer/sigint.html)):

- **The child was killed by SIGINT** (`WIFSIGNALED` and `WTERMSIG == SIGINT`): bash assumes the user wants everything to stop, so it aborts the loop or script.
- **The child exited normally, even with code 130**: bash assumes the child handled Ctrl+C on purpose, the way an editor or `less` would. So it carries on with the next iteration.

`os.Exit(130)` is a normal exit. 130 is only the number a shell *shows* for a process killed by SIGINT (128 + 2). Returning it yourself doesn't make the parent see a signal death. That's why the loop doesn't stop.

## Fix: clean up, then re-raise SIGINT

After cleanup, put back the default SIGINT behaviour and send SIGINT to your own process, so it really dies from the signal:

```go
sigs := make(chan os.Signal, 1)
signal.Notify(sigs, os.Interrupt)

go func() {
	<-sigs
	fmt.Fprintln(os.Stderr, "\ninterrupted, cleaning up…")

	// A second Ctrl+C during cleanup should force-exit.
	go func() { <-sigs; os.Exit(130) }()

	done := make(chan struct{})
	go func() { cleanup(); close(done) }()
	select {
	case <-done:
	case <-time.After(5 * time.Second): // bound cleanup time
	}

	signal.Reset(os.Interrupt) // back to the default action: terminate
	syscall.Kill(syscall.Getpid(), syscall.SIGINT)

	// The signal arrives asynchronously, so wait for it here.
	// The exit below is only a fallback in case it never arrives.
	time.Sleep(time.Second)
	os.Exit(130)
}()
```

Notes:

- **Don't let `main` return or call `os.Exit` before the signal is delivered.** If you do, you're back to a normal exit. That's the reason for the short wait after `Kill`.
- **Windows:** `syscall.Kill` and the 128+N convention don't exist there. Put the re-raise behind a `//go:build !windows` build tag, and on Windows just exit with your own code.
- **The no-cleanup alternative:** a Go program that never calls `signal.Notify` already dies from SIGINT correctly. You only need the re-raise because you catch the signal.
- **Exit 130 is still right in one case:** when your own code handles a Ctrl+C keypress that never became a signal. For example, a cancelled prompt, or a TUI in raw mode where Ctrl+C arrives as a key. There's no real SIGINT to re-raise then, and exiting non-zero still stops `tool && next`.

## Check the fix

```sh
for i in 1 2 3; do ./yourtool; echo "iteration $i done"; done
```

Press Ctrl+C during the first run. Before the fix, iterations 2 and 3 still run. After the fix, the loop stops, and `echo $?` after a single interrupted run still prints 130 (the shell reports it for you).
