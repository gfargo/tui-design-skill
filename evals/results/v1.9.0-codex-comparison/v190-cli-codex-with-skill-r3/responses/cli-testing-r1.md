Test the **built binary as a black box**, asserting **stdout, stderr, and the exact exit code separately**. For a one-shot CLI, ordinary pipes are the right default; you usually don’t need a PTY.

Use a small test matrix:

| Case | What to assert |
|---|---|
| Success | Expected stdout, empty stderr, code `0` |
| Invalid arguments | Empty stdout, useful stderr, documented usage-error code |
| Runtime failure | Expected stderr and exact failure code |
| `--help` / `--version` | Expected stdout, empty stderr, code `0` |
| Piped input / EOF | Correct result; no unexpected prompt or hang |
| `NO_COLOR=1` | Plain output with no ANSI escapes |
| `--json`, if supported | Valid JSON with expected fields; diagnostics stay on stderr |

**In Go, `os/exec` is enough for a small suite.** Build once per suite, then use a helper like this:

```go
func runCLI(t *testing.T, bin string, args ...string) (string, string, int) {
	t.Helper()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, bin, args...)
	cmd.Env = append(os.Environ(), "NO_COLOR=1")
	cmd.Stdin = strings.NewReader("") // EOF, no terminal

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

Compare short output inline; put longer help or text output in separate `.stdout.golden` and `.stderr.golden` files. Preserve whitespace and trailing newlines—avoid `TrimSpace`, which hides regressions. For JSON, decode and compare values unless formatting itself is part of your contract.

For many filesystem-oriented scenarios, use **[`testscript`](https://github.com/rogpeppe/go-internal/tree/master/testscript)**. It gives you readable scripts and isolated fixtures. One important catch: **`! exec` checks only that a command failed**, so add a custom assertion for exact exit codes.

Keep tests deterministic: isolate config and working directories, control relevant environment variables, and fix timestamps or randomness. Test non-TTY behavior both with `NO_COLOR` unset and with `NO_COLOR=1`.

Finally, keep parsing and business-logic unit tests underneath this suite. A `run(args, stdin, stdout, stderr) int` function with `os.Exit` only in `main` makes those cheap, while binary tests verify the actual process contract.