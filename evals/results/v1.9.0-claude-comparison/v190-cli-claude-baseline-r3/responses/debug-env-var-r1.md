I'd advise against using plain `DEBUG`. Use a namespaced variable plus a flag instead.

**Why not `DEBUG`:**
- **It's already widely used.** The `debug` npm package uses `DEBUG=namespace:*` patterns, and many other tools read it too. People often have `DEBUG=express:*` or `DEBUG=1` set for something else, and your CLI would start printing stack traces they never asked for.
- **Its meaning isn't clear.** Tools treat `DEBUG=1`, `DEBUG=true`, `DEBUG=*` and `DEBUG=myapp` differently, so users can't predict what your CLI will do.
- **It leaks into child processes.** If your CLI runs other tools, they'll see `DEBUG` too.

**What I'd do instead:**
1. **Add a flag: `--debug` (or `--verbose`/`-v`).** Users can find it in `--help`, and it applies only to the command they typed.
2. **Add a namespaced variable: `MYCLI_DEBUG=1`.** This is for CI or other places where you can't easily change the command. Prefixing with the tool name is what tools like `NODE_DEBUG`, `GIT_TRACE` and `RUST_BACKTRACE` do.
3. **Decide which wins.** The flag should override the variable, and the variable should override the default.
4. **Optionally, also honor `DEBUG`, but only if it names your tool** (e.g. `DEBUG=mycli` or `DEBUG=mycli:*`). Users of the `debug` package expect this, and it avoids collisions.

**For the default error output:**
- Show a short, readable message and a hint like `Run with --debug for the full stack trace.`
- Treat stack traces for unexpected errors (bugs) differently from expected ones like "file not found". Expected errors never need a trace. For bugs, you might always print one, or point users to a log file.
- Send debug output to stderr so it doesn't mix with stdout when someone pipes your output.

If you tell me the language or CLI framework you're using (Node with commander/yargs/oclif, Python with click/typer, Go with cobra, etc.), I can show you how to set this up.
