Test the **built binary as a black box**, asserting **stdout, stderr, and the exact exit code separately**. For a one-shot CLI, ordinary subprocess tests are the right starting point.

Use two layers:

- **Fast Go tests:** expose `run(args, stdin, stdout, stderr) int` and test it with buffers. Keep `os.Exit` in `main`.
- **Binary integration tests:** build once, then run representative commands with `os/exec`. These catch stream wiring and actual process exits. Avoid `go run`: it obscures your program’s exit status.

A subprocess assertion can look like this; `bin` is the path to your built executable:

```go
func checkCLI(t *testing.T, bin string, args []string,
	wantCode int, wantOut, wantErr string,
) {
	t.Helper()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, bin, args...)
	var stdout, stderr bytes.Buffer
	cmd.Stdout, cmd.Stderr = &stdout, &stderr

	err := cmd.Run()
	if ctx.Err() != nil {
		t.Fatalf("command timed out: %v", ctx.Err())
	}

	code := 0
	if err != nil {
		var exitErr *exec.ExitError
		if !errors.As(err, &exitErr) {
			t.Fatalf("could not run command: %v", err)
		}
		code = exitErr.ExitCode()
	}

	if code != wantCode ||
		stdout.String() != wantOut ||
		stderr.String() != wantErr {
		t.Fatalf(
			"got code=%d stdout=%q stderr=%q\nwant code=%d stdout=%q stderr=%q",
			code, stdout.String(), stderr.String(),
			wantCode, wantOut, wantErr,
		)
	}
}
```

Cover this small contract matrix first:

| Case | stdout | stderr | Exit |
|---|---|---|---|
| Success | Result | Empty unless documented | `0` |
| `--help`, `--version` | Requested information | Empty | `0` |
| Invalid arguments | Empty | Usage diagnostic | Typically `2` |
| Operational failure | Empty unless partial results are documented | Actionable error | Typically `1` |
| Empty result | Documented empty representation | Usually empty | Documented behavior |

Also verify:

- **Non-TTY behavior:** subprocess buffers provide this naturally; no prompts, spinners, or escape sequences.
- **`NO_COLOR=1`:** output remains plain. Test separately from automatic non-TTY suppression.
- **JSON:** decode it and assert structure; ensure stdout contains no diagnostics.
- **Determinism:** isolate config/home directories, fix time and locale where relevant, and sort unordered results.
- **Text goldens:** compare exact bytes, including trailing newlines. Review golden changes as interface changes.

For a larger fixture suite, use Go’s [`testscript`](https://pkg.go.dev/github.com/rogpeppe/go-internal/testscript). Its `.txtar` files make command/output cases readable, but **`! exec` checks only that execution failed**; add an exact-exit-code assertion.

Add PTY tests only if you have behavior that specifically depends on a real terminal.