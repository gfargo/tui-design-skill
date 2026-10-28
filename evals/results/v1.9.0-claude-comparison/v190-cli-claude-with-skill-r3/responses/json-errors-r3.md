Write failures to **stderr** as one compact JSON line. Leave stdout empty, exit with the same non-zero code the human-readable error would use, and include a stable machine `code` for scripts to branch on. After that, treat the JSON schema as a public API: you can add fields, but never take anything away or change what it means.

## Failures under `--json`

```
$ mytool export --json > out.json
$ echo $?
73
$ cat out.json          # empty
$ # stderr:
{"schema_version":1,"error":{"code":"permission_denied","message":"cannot write out.txt: permission denied","hint":"chmod +w out.txt"}}
```

The rules:

- **stdout carries only results.** On failure it stays empty. Then `mytool --json | jq …` never gets an error object mixed in with real data, and `[ -s out.json ]` tells you whether it worked.
- **One compact line on stderr.** Don't pretty-print it, so a script can read the last line of stderr and parse it.
- **Same exit code as human mode.** `--json` changes the format, not what happened. Use 2 for usage errors, your own documented codes from 3 to 123, and never 124 or higher. Exit 130 if a prompt was cancelled.
- **`code` is the contract and `message` is not.** Scripts branch on `"permission_denied"`, so you can reword the message any time. Never rename a code.
- **Version the error object** with the same `schema_version` as the success output.
- **No stack traces** unless `--debug` or `MYTOOL_DEBUG=1` is set. If they're on, put the trace in an extra field, not in `message`.
- **Usage errors count too.** If a bad flag comes alongside `--json`, emit the JSON error and exit 2 instead of printing help text.
- **Warnings, progress and limit notes** stay on stderr as they do now. Never send them to stdout, use no color, and don't page the output.

Tools don't agree on this. npm prints `{"error":…}` on stdout, the AWS CLI's `--cli-error-format json` writes to stderr, and gh, cargo and kubectl don't produce structured errors at all. I recommend stderr because then stdout contains only results.

**Streaming (NDJSON) output:** records already written stay valid on stdout, the error line goes to stderr, and the exit code is non-zero. That way a consumer knows the stream was cut off and didn't just end normally. (The guide doesn't spell this out; it follows from the stdout-is-results rule.)

## Compatibility rules

**Shape**
- For a bounded result, emit one JSON document.
- For unbounded or streaming results, emit NDJSON: one compact object per line and nothing else on stdout.
- Pretty-print only when stdout is a TTY. The content must be identical either way; only the whitespace changes.
- If results are paged, put the cursor inside the document (`{"items":[…],"next_cursor":"…"}`) rather than in stderr text.

**Changes**
- **Additive only.** You can add fields. Never remove, rename, change the type of, or change the meaning of an existing one. Error `code` values count as part of the schema.
- **Document that consumers must ignore unknown fields**, as Terraform's JSON format does. This rule is what makes adding fields safe.
- If a change would break consumers, bump `schema_version`. Give it a deprecation period of at least one release: print a stderr notice and keep the old field working until the next major version.
- Human-readable output can change freely; `--json` output can't.

**Values**
- Times are RFC 3339 in UTC with a `Z`, e.g. `2026-04-29T15:25:16Z`.
- Numbers are JSON numbers in raw units (`1200000`), never `"1.2 MB"` or `"1,234"`.
- Never put color codes, truncation or locale formatting in JSON values.

## Lock it in with tests

Write golden tests against the built binary that check all three channels (stdout, stderr and the exit code) for both a success and a failure under `--json`. Run them with no TTY and with `NO_COLOR` set. For example, in Go's `testscript`:

```
! exec mytool export --json
! stdout .
stderr '^\{"schema_version":1,"error":\{"code":"permission_denied"'
```

`! exec` only asserts that the exit code is non-zero, so add a small custom command if you need to check the exact code. Freezing a golden file of the success schema is a cheap way to catch an accidental rename before it ships.

If you tell me the language or CLI framework, I can show where to hook this in so every error path goes through one JSON emitter.
