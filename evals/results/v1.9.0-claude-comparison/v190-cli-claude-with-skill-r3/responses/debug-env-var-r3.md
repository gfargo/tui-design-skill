No. Don't read plain `DEBUG`. Use a `--debug` flag, plus an environment variable with your tool's name in it, like `MYTOOL_DEBUG=1`.

**Why not `DEBUG`:** in practice, Node's popular `debug` package owns that variable, and people set it in their shell profiles and CI configs.
- Someone who sets `DEBUG=*` to debug some other tool would also get your stack traces dumped into their output, without asking for them.
- Someone who sets `DEBUG=1` expecting your tool to react would get nothing from the `debug` package, because it reads `DEBUG` as a list of name patterns and `1` matches nothing. So the same variable would mean different things to different tools on the same machine.

A name with your tool's prefix belongs only to you, so it can't collide.

**How to set it up:**
- **Default:** catch the errors you expect and print a short, readable message. The line that reports the failure starts with `error:`, and the fix command (or a docs link if there's no fix) goes on the last line, where the eye lands. Never show a raw stack trace by default.
- **`--debug`:** prints the full stack trace and any internal detail. Log-style labels and timestamps are fine in this mode.
- **`MYTOOL_DEBUG=1`:** does the same thing as `--debug`. It's useful in CI, or when the command runs inside a script you can't easily edit.
- **Keep it separate from `-v`/`--verbose`.** Verbose means more progress output; debug means internals. If you want levels, `-vv`/`-vvv` can step up gradually, but stack traces should stay behind `--debug`.

**One exception:** while you're developing a Bubble Tea TUI, the common pattern is `DEBUG=1 go run .` with logs written to a file you watch with `tail -f debug.log`. That's acceptable because it's for you as the developer, not something users see. For behavior you ship, use your own prefixed variable.
