Use **two layers**: table tests against a `run` function for most cases, and `testscript` against the real binary for the stdout/stderr/exit-code contract. Assert all three channels in every case, and add cases with no TTY and with `NO_COLOR`.

## 1. Move `main` into a testable `run` function

Keep `main` to one line so the real logic can be tested without starting a process:

```go
func main() {
    os.Exit(run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr, os.Getenv))
}

func run(args []string, stdin io.Reader, stdout, stderr io.Writer, getenv func(string) string) int {
    // parse flags, do work, write results to stdout, diagnostics to stderr
    // return 0 / 1 / 2 (usage) / documented domain codes
}
```

Then write a fast table test that checks all three outputs together:

```go
func TestRun(t *testing.T) {
    tests := []struct {
        name               string
        args               []string
        env                map[string]string
        wantCode           int
        wantOut, wantErr   string
    }{
        {"greets", []string{"ann"}, nil, 0, "hello ann\n", ""},
        {"missing file", []string{"bad"}, nil, 1, "", "error: cannot read bad: no such file\n"},
        {"bad flag", []string{"--nope"}, nil, 2, "", "error: unknown flag --nope\n"},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            var out, errb bytes.Buffer
            code := run(tt.args, strings.NewReader(""), &out, &errb,
                func(k string) string { return tt.env[k] })
            if code != tt.wantCode || out.String() != tt.wantOut || errb.String() != tt.wantErr {
                t.Errorf("got (%d, %q, %q), want (%d, %q, %q)",
                    code, out.String(), errb.String(), tt.wantCode, tt.wantOut, tt.wantErr)
            }
        })
    }
}
```

Because `stdout` here is a `bytes.Buffer` and not a TTY, this covers the piped/no-TTY behavior for free.

## 2. Black-box tests with `testscript`

[`testscript`](https://github.com/rogpeppe/go-internal/tree/master/testscript) (from `rogpeppe/go-internal`) runs your command as a real subprocess from `.txtar` scripts. It's the most common Go tool for this.

```go
func TestMain(m *testing.M) {
    testscript.Main(m, map[string]func(){
        "mytool": func() { os.Exit(run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr, os.Getenv)) },
    })
}

func TestScripts(t *testing.T) {
    testscript.Run(t, testscript.Params{
        Dir:  "testdata",
        Cmds: map[string]func(*testscript.TestScript, bool, []string){
            "exitcode": cmdExitCode,
        },
    })
}
```

```
# testdata/basic.txtar
exec mytool ann
stdout '^hello ann\n$'
! stderr .

exitcode 1 mytool bad
! stdout .
stderr '^error: cannot read bad: no such file\n$'

exitcode 2 mytool --nope

env NO_COLOR=1
exec mytool ann
! stdout '\x1b'
```

**One catch:** `! exec` only checks that the exit code is non-zero, so it can't tell 1 from 2. If you care about the exact code, add a small custom command:

```go
// exitcode N cmd args... — run cmd and require exit status N.
func cmdExitCode(ts *testscript.TestScript, neg bool, args []string) {
    if neg || len(args) < 2 {
        ts.Fatalf("usage: exitcode N cmd [args...]")
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
        ts.Fatalf("exit code: got %d, want %d", got, want)
    }
}
```

`ts.Exec` captures stdout and stderr, so the `stdout`/`stderr` lines after `exitcode` still check that run's output. I wrote this helper from the `testscript` API and haven't run it, so check it against the go-internal version you use.

## What to cover

- **Every exit code you document**: success, general failure (1), usage error (2), and any domain codes. Keep custom codes in 3–123. Codes from 124 up are already used by `timeout`, the shell and signals, so don't use them.
- **Results go to stdout, diagnostics to stderr.** Every failure case should check `! stdout .`, and every success case should check `! stderr .` unless you expect warnings. These checks catch a stray `fmt.Println` debug line.
- **No TTY**: tests already run without one. Assert that piped output has no colors, spinners, progress bars or prompts.
- **`NO_COLOR=1`**: no `\x1b` bytes in the output.
- **`--json`, if you have it**: it should parse, and errors should still go to stderr with a non-zero exit code.
- **Golden files**: store plain text only, never color escapes, so they stay readable and stable.

Most cases belong in the fast `run` table tests. Keep the testscript suite small, with one or two scripts per subcommand covering the stream/exit-code contract and anything that depends on environment variables, files or stdin. You don't need a PTY or a terminal emulator for a one-shot CLI.
