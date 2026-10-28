I'd use two layers of tests: fast in-process tests for most cases, and a small set of end-to-end tests that run the real binary.

## 1. Make `main` a thin wrapper around a testable `run`

This change matters most. `os.Exit` and the global `os.Stdout` make code hard to test, so keep them out of your logic:

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
		return 2 // usage error
	}
	// ... real work, writing to stdout/stderr ...
	if err := doThing(stdout, *verbose); err != nil {
		fmt.Fprintln(stderr, "error:", err)
		return 1
	}
	return 0
}
```

Use `flag.ContinueOnError` on your own `FlagSet`. The default `flag.CommandLine` calls `os.Exit` on bad flags. If you use Cobra, call `cmd.SetArgs`, `SetOut` and `SetErr`, and have `Execute()` return an error instead of exiting.

Then write table-driven tests:

```go
func TestRun(t *testing.T) {
	tests := []struct {
		name       string
		args       []string
		stdin      string
		wantCode   int
		wantStdout string
		wantStderr string // substring match is usually enough for errors
	}{
		{"help", []string{"-h"}, "", 0, "", "Usage"},
		{"bad flag", []string{"--nope"}, "", 2, "", "flag provided but not defined"},
		{"happy path", []string{"input.txt"}, "", 0, "ok\n", ""},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var out, errOut bytes.Buffer
			code := run(tt.args, strings.NewReader(tt.stdin), &out, &errOut)
			if code != tt.wantCode {
				t.Errorf("exit code = %d, want %d\nstderr: %s", code, tt.wantCode, errOut.String())
			}
			if out.String() != tt.wantStdout {
				t.Errorf("stdout = %q, want %q", out.String(), tt.wantStdout)
			}
			if !strings.Contains(errOut.String(), tt.wantStderr) {
				t.Errorf("stderr = %q, want substring %q", errOut.String(), tt.wantStderr)
			}
		})
	}
}
```

These tests are fast, can use `t.Parallel()` if you avoid globals, count toward coverage, and are easy to debug.

**Golden files for large output:** store expected output in `testdata/<name>.golden` and add an `-update` flag that rewrites the files:

```go
var update = flag.Bool("update", false, "update golden files")
// in the test:
golden := filepath.Join("testdata", tt.name+".golden")
if *update { os.WriteFile(golden, out.Bytes(), 0o644) }
want, _ := os.ReadFile(golden)
```

Run `go test -update`, then review the diff in git.

## 2. End-to-end tests with `testscript`

For tests against the real binary, I recommend [`github.com/rogpeppe/go-internal/testscript`](https://pkg.go.dev/github.com/rogpeppe/go-internal/testscript). The Go team tests the `go` command itself this way. Each test is a small script that runs commands and checks their output and exit status:

```go
// main_test.go
func TestMain(m *testing.M) {
	testscript.Main(m, map[string]func(){
		"mytool": main, // makes "mytool" a command inside scripts
	})
}

func TestScripts(t *testing.T) {
	testscript.Run(t, testscript.Params{Dir: "testdata/script"})
}
```

```
# testdata/script/basic.txtar

# success case
exec mytool input.txt
stdout '^ok$'
! stderr .

# missing file: exit code must be non-zero
! exec mytool missing.txt
stderr 'no such file'

# exact exit code check
exec sh -c 'mytool --nope; echo "code=$?"'
stdout 'code=2'

-- input.txt --
some fixture content
```

Each script runs in its own temp directory, and files after `-- name --` are created as fixtures. You can also use `cmp stdout want.txt` for exact comparisons and `env` to set environment variables. This covers what `run()` tests can't reach: the real `os.Exit` path, signal and stdin behavior, and file system side effects.

## Other tips

- **Coverage for e2e runs:** since Go 1.20, you can build with `go build -cover` and set `GOCOVERDIR` to collect coverage from the real binary.
- **Make output deterministic:** inject the clock, sort map iteration, and check `NO_COLOR` or whether stdout is a TTY so tests get plain output.
- **Define exit codes as constants** (`exitOK = 0`, `exitErr = 1`, `exitUsage = 2`) and test that each one is reachable.
- **Don't test the same thing twice:** put most cases in `run()` table tests, and keep a few testscript files for full-binary smoke tests.

I'd start with section 1 because it gives you the most for the least work. Add testscript once you want to check the real binary's behavior.
