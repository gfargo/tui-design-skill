Test the compiled binary from the outside with `testscript`, and check three things on every case: stdout, stderr, and the exit code. Underneath that, keep a few plain Go unit tests for the logic. You don't need a PTY or a TUI harness for a one-shot command.

## 1. Make `main` a thin wrapper

```go
// main.go
func main() { os.Exit(run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr)) }

func run(args []string, stdin io.Reader, stdout, stderr io.Writer) int {
    // parse flags, do the work, write results to stdout,
    // diagnostics to stderr, return the exit code
}
```

With this shape, ordinary table tests can call `run` and check the returned code and two `bytes.Buffer`s. They run fast and need no subprocess, so use them for parsing and edge cases. Also make sure nothing calls `os.Exit` or `log.Fatal` outside `main`. Otherwise exit paths skip your tests and your cleanup.

## 2. Use testscript for the user-facing contract

`github.com/rogpeppe/go-internal/testscript` runs your real `main` as a subprocess from `.txtar` scripts. You don't have to build or install anything first.

```go
// main_test.go
func TestMain(m *testing.M) {
    testscript.Main(m, map[string]func(){
        "mytool": func() { os.Exit(run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr)) },
    })
}

var update = flag.Bool("update", false, "update testscript cmp files")

func TestScripts(t *testing.T) {
    testscript.Run(t, testscript.Params{
        Dir:           "testdata/script",
        UpdateScripts: *update,
        Cmds:          map[string]func(*testscript.TestScript, bool, []string){"exitcode": cmdExitCode},
    })
}

// exitcode N cmd args... : run cmd and require exactly exit status N.
func cmdExitCode(ts *testscript.TestScript, neg bool, args []string) {
    if neg || len(args) < 2 {
        ts.Fatalf("usage: exitcode N command [args...]")
    }
    want, err := strconv.Atoi(args[0])
    ts.Check(err)
    got := 0
    if err := ts.Exec(args[1], args[2:]...); err != nil {
        var ee *exec.ExitError
        if !errors.As(err, &ee) {
            ts.Fatalf("exec %s: %v", args[1], err)
        }
        got = ee.ExitCode()
    }
    if got != want {
        ts.Fatalf("exit code = %d, want %d", got, want)
    }
}
```

You need the custom command because the built-in `! exec` only checks for a non-zero exit. It can't tell a usage error (2) from a runtime failure (1) or one of your own codes. `ts.Exec` still records stdout and stderr, so the usual `stdout`, `stderr` and `cmp` assertions work after `exitcode`.

```
# testdata/script/basic.txtar

# success: result on stdout, nothing on stderr
exec mytool greet ann
stdout '^hello ann\n$'
! stderr .

# usage error: exit 2, nothing on stdout, help hint on stderr
exitcode 2 mytool --bogus
! stdout .
stderr 'unknown flag'

# runtime failure: exit 1, message on stderr only
exitcode 1 mytool read missing.txt
! stdout .
stderr '^error: cannot read missing.txt: no such file'

# no TTY under the runner, plus NO_COLOR: no escape codes
env NO_COLOR=1
exec mytool greet ann
! stdout '\x1b'

# exact output: compare against the golden file below
exec mytool list --json
cmp stdout want.json

-- want.json --
[{"name":"ann"}]
```

## What to cover

- **All three channels in every case.** Assert that an empty stream is empty (`! stdout .`, `! stderr .`). The bug that actually hurts scripts is a warning ending up on stdout and breaking a pipe or `jq`.
- **Each exit code you document.** At minimum that's 0 for success, 1 for general failure and 2 for usage errors. If you use domain codes, keep them in 3–123. 124–255 already mean timeouts, shell errors and signals (130 is Ctrl+C), so don't use them.
- **Non-TTY and `NO_COLOR` behavior.** Tests run without a TTY, so colors and spinners should switch off automatically. Add a `NO_COLOR` case anyway, and keep golden files as plain text with no ANSI codes.
- **Machine-readable output.** If you have `--json`, check it byte for byte with `cmp`, including the error path. Decide whether errors are JSON on stderr or plain text, and test whichever you choose.
- **Stdin.** If the tool reads from a pipe, cover that with `stdin input.txt` before an `exec`.

Run `go test ./... -update` to rewrite the `cmp` files in the scripts after an intentional output change. Review that diff as carefully as a code diff.
