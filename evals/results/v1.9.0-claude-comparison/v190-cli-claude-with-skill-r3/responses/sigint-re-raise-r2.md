The problem is that `os.Exit(130)` looks like a normal exit to the shell. To bash, your program caught the signal and handled it.

## Why the loop keeps going

When you press Ctrl+C, the terminal sends SIGINT to the whole foreground process group. That includes your program and the bash running the loop. Bash doesn't stop the loop straight away. It waits for the child and then looks at how the child ended (the "wait and cooperative exit" rule; [Cracauer's write-up](https://www.cons.org/cracauer/sigint.html) explains it):

- **If the child was killed by SIGINT** (`WIFSIGNALED`), bash assumes the user wants to stop and ends the loop or script.
- **If the child exited normally**, bash assumes the child handled Ctrl+C itself, the way `vim` or `less` do, and the loop continues. Exit code 130 counts as a normal exit.

The shell reports 130 (128 + 2) when a child dies from SIGINT, but returning 130 yourself is not the same thing. The parent can tell the two apart.

## The fix: re-raise the signal

After cleanup, restore the default SIGINT handler and send SIGINT to your own process. The kernel then kills the process with the signal, and bash sees a real death-by-signal.

```go
sigCh := make(chan os.Signal, 1)
signal.Notify(sigCh, os.Interrupt)

go func() {
	<-sigCh
	fmt.Fprintln(os.Stderr, "\nInterrupted, cleaning up…")

	// Second Ctrl+C during cleanup forces exit
	go func() {
		<-sigCh
		os.Exit(130)
	}()

	cleanup() // keep this bounded with a timeout

	signal.Reset(os.Interrupt)                    // restore the default action (terminate)
	syscall.Kill(syscall.Getpid(), syscall.SIGINT) // die by the signal
	time.Sleep(time.Second)                       // delivery is async; give it a moment
	os.Exit(130)                                  // fallback only
}()
```

Notes:

- **`signal.Reset` must come before the `Kill`.** If it doesn't, your handler catches the signal again and the process never dies from it.
- **The second-Ctrl+C goroutine is there so a stuck cleanup can't trap the user.** The `os.Exit(130)` inside it is the forced quit.
- **Signal delivery is asynchronous.** The short sleep keeps the process alive until the signal arrives, and `os.Exit(130)` runs only if it never does.
- **This is POSIX only.** Windows has no SIGINT re-raise, so put this behind a build tag (`//go:build !windows`). On Windows, don't turn Ctrl+C into 130.
- **If you don't need cleanup, don't call `signal.Notify` for SIGINT at all.** Go's default behavior already dies from the signal correctly.

## How to check it

```sh
for i in 1 2 3; do ./mytool; echo "iteration $i done"; done
```

Press Ctrl+C during the first run. With the fix, the loop stops and you won't see "iteration 1 done". In an interactive shell, `echo $?` after a single interrupted run should still print 130, because bash now reports it as 128 + SIGINT.

Exit 130 is still correct in one case: when the user cancels an interactive prompt, for example with Esc or a prompt library that turns Ctrl+C into an error. There, no real signal reached your process, so a plain `os.Exit(130)` is the right abort code.
