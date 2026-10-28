Test the CLI as a black box using [`testscript`](https://github.com/rogpeppe/go-internal) (`github.com/rogpeppe/go-internal/testscript`). Under it, add a thin layer of in-process table tests. Every case should check three things: **stdout, stderr, and the exit code**.

## 1. Make `main` a thin wrapper

Put everything in a function that takes its streams and returns an exit code. Then `main` only does this:

```go
func main() {
	os.Exit(run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr))
}

func run(args []string, stdin io.Reader, stdout, stderr io.Writer) int {
	// parse flags, do work, write results to stdout, diagnostics to stderr
	// return 0 / 1 / 2 (usage) / documented domain codes
}
```

This gives you cheap, fast table tests for parsing and edge cases, with no binary and no subprocess:

```go
func TestRun(t *testing.T) {
	tests := []struct {
		name             string
		args             []string
		code             int
		stdout, stderr   string
	}{
		{"greets", []string{"ann"}, 0, "hello ann\n", ""},
		{"missing file", []string{"bad"}, 1, "", "error: cannot read bad: no such file\n"},
		{"bad flag", []string{"--nope"}, 2, "", "error: unknown flag --nope\n"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var out, errb bytes.Buffer
			code := run(tt.args, strings.NewReader(""), &out, &errb)
			if code != tt.code || out.String() != tt.stdout || errb.String() != tt.stderr {
				t.Errorf("got (%d, %q, %q), want (%d, %q, %q)",
					code, out.String(), errb.String(), tt.code, tt.stdout, tt.stderr)
			}
		})
	}
}
```

## 2. Use testscript for the real contract

testscript runs your command as a subprocess. Each case lives in a readable `.txtar` file under `testdata/`. No separate `go build` is needed: `TestMain` registers your `main` as a command.

```go
// main_test.go
func TestMain(m *testing.M) {
	testscript.Main(m, map[string]func(){
		"mytool": main,
	})
}

func TestScripts(t *testing.T) {
	testscript.Run(t, testscript.Params{
		Dir: "testdata/script",
		Cmds: map[string]func(*testscript.TestScript, bool, []string){
			"exitcode": cmdExitCode,
		},
	})
}
```

**About exit codes:** testscript's built-in `! exec` only checks that the code is *non-zero*. If you care whether it was 1, 2, or 3, add a small custom command:

```go
// exitcode N cmd args...  — runs cmd, asserts its exact exit status,
// and keeps stdout/stderr available for the next assertions.
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

A script then reads like this:

```
# testdata/script/basic.txtar

# success: result on stdout, nothing on stderr
exec mytool ann
stdout '^hello ann\n$'
! stderr .

# missing file: exit 1, nothing on stdout, one-line error on stderr
exitcode 1 mytool bad
! stdout .
stderr '^error: cannot read bad: no such file\n$'

# usage error is 2, not 1
exitcode 2 mytool --nope
stderr 'unknown flag'

# no color escapes when NO_COLOR is set
env NO_COLOR=1
exec mytool ann
! stdout '\x1b'

# input fixtures can live in the same file
exec mytool input.txt
cmp stdout want.txt

-- input.txt --
ann
-- want.txt --
hello ann
```

## What to cover

- **All three channels in every case.** Write `! stderr .` on success and `! stdout .` on failure. Most stream bugs are output landing on the wrong one: a warning on stdout breaks `$(mytool)` and `| jq`.
- **Distinct exit codes.** Use 0 for success, 1 for generic failure, and 2 for usage errors (Go's `flag` already uses 2). Your own documented codes go in the 3–123 range. Never use 124 or higher; shells and signals own those.
- **No TTY.** This is the default under `go test`, so your tests already run the piped path. Make sure that path doesn't print colors, spinners, or prompts. If the tool prompts, add a case showing it fails cleanly instead of hanging when stdin isn't a terminal.
- **`NO_COLOR`.** Keep golden files plain text. Don't store escape sequences in them, or they'll break whenever color detection changes.
- **`--json` output, if you have it.** That output is the stable API scripts rely on, so check it with exact matches (`cmp stdout want.json`), not loose regexes.
- **`--help` and `--version`.** Both should write to stdout and exit 0. A usage error should write help or a hint to stderr and exit 2.

## What you can skip

You don't need a pseudo-terminal (PTY) harness, teatest, or VHS for a one-shot CLI. Those are for full-screen or interactive UIs. In-process `run()` tests for the logic plus a few dozen `.txtar` scripts for the contract cover what you said you care about.
