Test the **built binary as a black box**, checking **stdout, stderr, and the exact exit code separately**. For a one-shot CLI, ordinary subprocess tests are usually enough; add PTY tests only if behavior depends on a real terminal.

In Go, start with `testing` and `os/exec`. Build once for the suite, then run table-driven cases against that executable. Avoid `go run`: it adds build overhead and can obscure the program’s exit status.

A small helper makes the contract explicit:

```go
func runCLI(t *testing.T, binary string, args ...string) (string, string, int) {
	t.Helper()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, binary, args...)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()
	if ctx.Err() != nil {
		t.Fatalf("CLI timed out: %v", ctx.Err())
	}

	code := 0
	if err != nil {
		var exitErr *exec.ExitError
		if !errors.As(err, &exitErr) {
			t.Fatalf("could not run CLI: %v", err)
		}
		code = exitErr.ExitCode()
	}
	return stdout.String(), stderr.String(), code
}
```

Use cases like these, adjusted to your documented behavior:

| Case | stdout | stderr | Exit |
|---|---|---|---|
| Success | Expected result | Empty | `0` |
| `--help` | Help text | Empty | `0` |
| Invalid flag or missing argument | Empty | Usage diagnostic | `2` |
| Operational failure | Empty* | Useful error | `1` |
| `--json` | Valid JSON with expected fields | No diagnostic on success | `0` |
| Redirected output | Plain results, no escape sequences | Plain diagnostics | As appropriate |
| `NO_COLOR=1` | No color escapes | No color escapes | As appropriate |

\*If partial results are supported, test that contract explicitly.

For assertions:

- **Small output:** compare exact strings, including trailing newlines and empty streams.
- **Long help or reports:** use separate `.stdout.golden` and `.stderr.golden` files, plus an exact exit-code assertion.
- **JSON:** decode and compare values; avoid depending on whitespace or object-key order.
- **Changing values:** control clocks, fixtures, environment, configuration directories, and working directory. Normalize only unavoidable differences.

Run both a normal non-TTY case and an explicit `NO_COLOR=1` case. Don’t strip ANSI before checking plain output—that could hide a regression.

If the suite grows into many filesystem scenarios, use [`testscript`](https://pkg.go.dev/github.com/rogpeppe/go-internal/testscript). It provides readable scripts and isolated fixtures. One important detail: **`! exec` checks only that the command failed**, so add a custom assertion for exact exit codes.

Keep most logic tests fast by extracting a function such as `run(args, stdin, stdout, stderr) int`, with `os.Exit` confined to `main`. Retain binary tests to verify the actual stream wiring and process exit behavior.