**Short version:** when `--json` is set and the command fails, print nothing to stdout. Write one compact JSON error line to stderr and exit with the same non-zero code the human-readable error would use. The error needs a stable `code` that scripts can branch on. For compatibility, only ever add to the schema: never remove, rename, change the type of, or change the meaning of a field.

## What failures look like

```
$ mytool export out.txt --json
$ echo $?
77
```
stderr (one line):
```json
{"schema_version":1,"error":{"code":"permission_denied","message":"cannot write out.txt: permission denied","hint":"chmod +w out.txt"}}
```

The rules:

- **stdout stays results-only.** If `mytool --json | jq .items` fails, jq gets no input, rather than an error object it has to tell apart from real data. Tools don't agree on this: npm puts `{"error":…}` on stdout, the AWS CLI's `--cli-error-format json` uses stderr, and gh, cargo and kubectl don't emit structured errors at all. stderr is the choice that keeps stdout clean.
- **Same exit code as the human error.** Scripts that only check `$?` should behave identically with or without `--json`. Use 0 for success, 1 for a general failure, 2 for a usage error, and your own documented codes in 3–123. Don't use 124–255: `timeout`, the shell and signal exits already claim those.
- **`code` is the contract; `message` is not.** Scripts branch on `"permission_denied"`, `"not_found"` and so on. You can reword `message` whenever you like, so make sure nobody needs to parse it.
- **`hint` is optional.** Include it when you have a concrete fix. It's the same text as the `hint:` line in your human-readable error.
- **No stack traces** unless `--debug` (or `MYTOOL_DEBUG=1`) is set. Even then, keep them out of the default fields, for example in a separate `debug` field.
- **Version the error object together with the success schema.** One `schema_version` covers both.
- **Usage errors count too.** If `--json` was parsed before the bad flag, emit the JSON error with exit 2. Write your argument parser's error path so this case is handled, not left to its default text output.
- **Partial failures:** if some results were written but the run didn't finish (say 3 of 10 items failed), still exit non-zero. Never let a truncated result look like success.

## Compatibility rules for the output

Once `--json` ships, it's an API. Human-readable output can change freely; JSON output can't.

1. **Additive changes only.** You can add fields. You can never remove, rename, change the type of, or change the meaning of an existing field. Document that consumers must ignore fields they don't recognise (Terraform's JSON format states this rule outright). If you truly need a breaking change, bump `schema_version` and give a deprecation warning on stderr at least one release ahead.
2. **Shape depends on the result:**
   - Bounded result: one JSON document.
   - Unbounded or streaming result: NDJSON, meaning one compact object per line and nothing else on stdout. Then `jq` and `while read` can process it line by line. Flush after each line.
3. **Pretty-print only when stdout is a TTY.** Piped output is compact. Never send `--json` output through a pager, and never put ANSI color codes in it, whatever `--color` says.
4. **Typed values:**
   - Timestamps are RFC 3339 UTC with a `Z`: `"2026-04-29T15:25:16Z"`.
   - Numbers are JSON numbers: `1234567`, not `"1.2 MB"` or `"1,234"`.
5. **Pagination goes in the document:** `{"items":[…],"next_cursor":"…"}`. NDJSON has no wrapper object, so print the truncation notice on stderr (`note: showing 30 of 1040 items; pass --limit N or --paginate for more`) and exit 0. Truncating because the user asked for a limit is not an error.
6. **Progress, warnings and logs always go to stderr.** One spinner frame on stdout breaks every consumer.

## Testing it

Test the built binary on all three channels (stdout, stderr and exit code), with no TTY attached:

```
# testscript
! exec mytool export /readonly/out.txt --json
! stdout .
stderr '"code":"permission_denied"'
```

Add a golden file for each success schema. A test that fails when a field disappears turns the "additive only" rule into something CI enforces rather than a promise.

If you'd like this mapped onto a specific stack (Go/cobra, Rust/clap, Python/Click or Typer, Node), tell me which one you're using. The detail that varies most between them is how to route argument-parser errors into the JSON path.
