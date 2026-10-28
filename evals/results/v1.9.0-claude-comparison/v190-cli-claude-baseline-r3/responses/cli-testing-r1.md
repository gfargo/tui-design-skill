The best approach is to make `main` very thin and test everything else as ordinary Go code. Add a few end-to-end tests on top of that to catch wiring bugs.

## 1. Make `main` a thin shell around a `run` function

```go
func main() {
    os.Exit(run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr))
}

func run(args []string, stdin io.Reader, stdout, stderr io.Writer) int {
    fs := flag.NewFlagSet("mytool", flag.ContinueOnError)
    fs.SetOutput(stderr)
    if err := fs.Parse(args); err != nil {
        return 2 // usage error
    }
    // ... real work, writing to stdout/stderr ...
    return 0
}
```

Rules that make this testable:
- No `os.Exit`, `log.Fatal`, or direct `os.Stdout` use anywhere below `main`.
- Use a local `FlagSet`, not the global `flag` package, so tests don't share state.
- Pass in anything else that comes from the environment, like env vars (`getenv func(string) string`), the working directory and the clock, so tests can control it.

## 2. Table-driven tests against `run`

```go
func TestRun(t *testing.T) {
    tests := []struct {
        name       string
        args       []string
        stdin      string
        wantCode   int
        wantStdout string
        wantStderr string
    }{
        {"help", []string{"-h"}, "", 0, "", "Usage"},
        {"bad flag", []string{"--nope"}, "", 2, "", "flag provided but not defined"},
        {"happy path", []string{"greet", "bob"}, "", 0, "hello bob\n", ""},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            var out, errb bytes.Buffer
            code := run(tt.args, strings.NewReader(tt.stdin), &out, &errb)
            if code != tt.wantCode {
                t.Errorf("exit = %d, want %d; stderr: %s", code, tt.wantCode, errb.String())
            }
            if tt.wantStdout != "" && out.String() != tt.wantStdout {
                t.Errorf("stdout = %q, want %q", out.String(), tt.wantStdout)
            }
            if !strings.Contains(errb.String(), tt.wantStderr) {
                t.Errorf("stderr = %q, want substring %q", errb.String(), tt.wantStderr)
            }
        })
    }
}
```

These tests are fast, run in parallel and measure coverage normally. Most of your tests should live here.

## 3. Golden files for large or structured output

If the output is long (tables, JSON, help text), compare it against files in `testdata/` and add an `-update` flag that rewrites them:

```go
var update = flag.Bool("update", false, "update golden files")
// ...
golden := filepath.Join("testdata", tt.name+".golden")
if *update { os.WriteFile(golden, out.Bytes(), 0o644) }
want, _ := os.ReadFile(golden)
```

Review the golden-file diffs in your PRs, because that's where output regressions will show up.

## 4. A few end-to-end tests with `testscript`

To test the real binary (actual `os.Exit`, signals, env, files), use `github.com/rogpeppe/go-internal/testscript`. It was built for exactly this kind of CLI and is what the Go toolchain uses to test itself:

```go
func TestMain(m *testing.M) {
    testscript.Main(m, map[string]func(){
        "mytool": main,
    })
}

func TestScripts(t *testing.T) {
    testscript.Run(t, testscript.Params{Dir: "testdata/script"})
}
```

`testdata/script/greet.txtar`:
```
exec mytool greet bob
stdout '^hello bob$'
! stderr .

! exec mytool --nope
stderr 'flag provided but not defined'

-- input.txt --
fixture files go here
```

Each script runs in its own temp directory. A `!` prefix asserts a non-zero exit. The scripts are easy to read, and adding a case doesn't require writing any Go.

## What to avoid

- Calling `main()` directly in tests and capturing output by swapping `os.Stdout`. It's fragile and can't be run in parallel.
- Using `go build` plus `exec.Command` for every case. It's slower and gives you no coverage. If you do it anyway, read the exit code with `errors.As(err, &exitErr); exitErr.ExitCode()`.

**Rough split:** put about 90% of your cases in table tests on `run`, use golden files for big outputs, and keep a small `testscript` suite for exit-code and integration behavior.
