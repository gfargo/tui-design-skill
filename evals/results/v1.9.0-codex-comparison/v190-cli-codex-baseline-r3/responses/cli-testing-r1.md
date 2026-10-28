Test it as a subprocess: build the binary once, run it with different arguments and stdin, then assert **stdout, stderr, and exit code separately**. This catches behavior that function-level tests miss, including `os.Exit`.

A small integration test using Go’s standard library:

```go
func TestCLI(t *testing.T) {
	bin := filepath.Join(t.TempDir(), "mycli")
	if runtime.GOOS == "windows" {
		bin += ".exe"
	}

	build := exec.Command("go", "build", "-o", bin, "./cmd/mycli")
	if out, err := build.CombinedOutput(); err != nil {
		t.Fatalf("build: %v\n%s", err, out)
	}

	tests := []struct {
		name, stdin string
		args        []string
		stdout      string
		stderr      string
		code        int
	}{
		{
			name:   "success",
			args:   []string{"hello"},
			stdout: "Hello!\n",
		},
		{
			name:   "invalid argument",
			args:   []string{"--unknown"},
			stderr: "unknown flag: --unknown\n",
			code:   2,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()

			cmd := exec.CommandContext(ctx, bin, tt.args...)
			cmd.Stdin = strings.NewReader(tt.stdin)

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

			if code != tt.code {
				t.Errorf("exit code: got %d, want %d\nstderr: %s",
					code, tt.code, stderr.String())
			}
			if got := stdout.String(); got != tt.stdout {
				t.Errorf("stdout: got %q, want %q", got, tt.stdout)
			}
			if got := stderr.String(); got != tt.stderr {
				t.Errorf("stderr: got %q, want %q", got, tt.stderr)
			}
		})
	}
}
```

Use your actual command path and expected output. The imports are `bytes`, `context`, `errors`, `os/exec`, `path/filepath`, `runtime`, `strings`, `testing`, and `time`.

A few practical choices:

- **Start with a small behavior matrix:** success, invalid arguments, missing input, and an operational failure.
- **Keep runs isolated:** use temporary working directories and control relevant environment variables, configuration, color, and locale.
- **Use golden files for lengthy output.** Compare bytes exactly when formatting is part of the contract; normalize only values that are intentionally variable.
- **Avoid `CombinedOutput` for assertions** when you care which stream receives a message.

If the cases grow into shell-like workflows involving files and multiple invocations, [`testscript`](https://pkg.go.dev/github.com/rogpeppe/go-internal/testscript) is worth considering. For a small one-shot CLI, table-driven subprocess tests are usually enough.