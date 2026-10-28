Split it into two layers: fast in-process unit tests for most cases, plus a thin end-to-end layer that checks the real binary.

## 1. Make `main` a thin wrapper around a testable `run`

This change does most of the work:

```go
// main.go
func main() {
	os.Exit(run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr))
}

func run(args []string, stdin io.Reader, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("mytool", flag.ContinueOnError)
	fs.SetOutput(stderr)
	verbose := fs.Bool("v", false, "verbose")
	if err := fs.Parse(args); err != nil {
		return 2
	}
	// ... real work, writing only to stdout/stderr ...
	return 0
}
```

The rules that make this work:
- Only `main` calls `os.Exit`. Everything else returns an error or an exit code. `log.Fatal` and `os.Exit` deep in the code make testing very hard.
- Pass in anything environmental: args, stdio, env vars (`getenv func(string) string`), the working directory, and time (if output includes timestamps).
- Use `flag.NewFlagSet` with `ContinueOnError`, not the global `flag` package. Global flags break when you call `run` more than once.

## 2. Table-driven tests against `run`

```go
func TestRun(t *testing.T) {
	tests := []struct {
		name       string
		args       []string
		stdin      string
		wantCode   int
		wantStdout string
		wantStderr string // or use strings.Contains for stderr
	}{
		{"no args", nil, "", 2, "", "usage:"},
		{"happy path", []string{"greet", "bob"}, "", 0, "hello bob\n", ""},
		{"bad input", []string{"parse"}, "{oops", 1, "", "invalid JSON"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var out, errb bytes.Buffer
			code := run(tt.args, strings.NewReader(tt.stdin), &out, &errb)
			if code != tt.wantCode {
				t.Errorf("exit code = %d, want %d", code, tt.wantCode)
			}
			if out.String() != tt.wantStdout {
				t.Errorf("stdout = %q, want %q", out.String(), tt.wantStdout)
			}
			if !strings.Contains(errb.String(), tt.wantStderr) {
				t.Errorf("stderr = %q, want substring %q", errb.String(), tt.wantStderr)
			}
		})
	}
}
```

These tests are fast, can run in parallel, and give you coverage. Most of your cases belong here.

**Golden files** help when output is large (tables, JSON, help text). Write the expected output to `testdata/<name>.golden` and add a `-update` flag that rewrites the files:

```go
var update = flag.Bool("update", false, "update golden files")
// ...
golden := filepath.Join("testdata", tt.name+".golden")
if *update { os.WriteFile(golden, out.Bytes(), 0o644) }
want, _ := os.ReadFile(golden)
```

Check the diffs in code review whenever you run with `-update`.

## 3. End-to-end tests with `testscript`

For the real binary, use [`github.com/rogpeppe/go-internal/testscript`](https://pkg.go.dev/github.com/rogpeppe/go-internal/testscript). It's the same approach the Go toolchain uses to test `go` itself, and it fits "output and exit codes" well:

```go
func TestMain(m *testing.M) {
	testscript.Main(m, map[string]func(){
		"mytool": func() { os.Exit(run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr)) },
	})
}

func TestScripts(t *testing.T) {
	testscript.Run(t, testscript.Params{Dir: "testdata/script"})
}
```

```
# testdata/script/greet.txtar
exec mytool greet bob
stdout '^hello bob$'
! stderr .

! exec mytool parse input.json
stderr 'invalid JSON'

-- input.json --
{oops
```

Each script runs in a fresh temp directory with its fixture files, and `!` asserts a non-zero exit. Scripts are easy to read and easy to add, so this layer catches problems with real process behavior: actual exit codes, signals, env handling, and file I/O. It's also nicer than shelling out with `exec.Command` and building the binary yourself.

## Practical tips
- **Define exit codes as named constants** (`exitOK`, `exitUsage = 2`, `exitError = 1`) and test them explicitly. Scripts that call your tool will depend on them.
- **Keep stdout and stderr separate.** Assert that errors don't leak into stdout, because people will pipe your output.
- **Normalize nondeterminism**: inject a clock, sort map iteration, and replace temp paths before comparing.
- **Assert stderr with substrings or regex** and stdout exactly. Error wording changes more often than data output does.
- Run with `-race` in CI if `run` uses goroutines.

**My recommendation:** do the `run()` refactor plus table tests first, since that covers about 90% of the value. Add `testscript` once you have a few flows that touch files or the environment.
