## Failures under `--json`

**Write the error as one compact JSON line on stderr. Leave stdout empty. Exit with the same non-zero code the human-mode error would use.**

```
$ mytool export --json > out.json
$ echo $?
77
$ cat out.json          # empty
$ # stderr:
{"schema_version":1,"error":{"code":"permission_denied","message":"cannot write out.txt: permission denied","hint":"chmod +w out.txt"}}
```

Tools don't agree on this. npm puts `{"error":…}` on stdout. The AWS CLI's `--cli-error-format json` writes to stderr. gh, cargo, and kubectl don't emit structured errors at all. Stderr is the better choice because stdout then only ever holds a result. A script that runs `mytool --json | jq .items` never has to parse an error object as if it were data.

Rules for the error object:

- **`code` is the field scripts branch on.** Make it a stable snake_case string such as `not_found`, `permission_denied` or `rate_limited`. Treat it as part of the API. Scripts should never parse `message`, and you can reword it whenever you like.
- **Keep `message` and `hint` in the same shape as the human error.** That's one lowercase line naming what failed and why, with the fix in `hint`.
- **The exit code still carries the meaning.** `--json` changes the format, not the outcome. If a usage error exits 2 in human mode, it exits 2 under `--json` too. Document your codes in `--help`. Use 0, 1, 2 and your own 3–123, and stay out of 124+, which belongs to `timeout`, the shell and signals.
- **No stack traces** unless `--debug` or `MYTOOL_DEBUG=1` is set. Even then, put them in a separate field or on separate stderr lines, not inside `message`.
- **Version the error with the success schema** (`schema_version`), so both evolve under one contract.
- **Partial failure is still failure.** If a batch half-succeeds, exit non-zero. Either emit the completed results plus the error, or emit nothing. Don't exit 0 with a short result. Never leave a truncated file at the final output path.
- **Prompts can't happen.** If an operation would need confirmation, `--json` can't answer it. Fail with a `code` like `confirmation_required` and a hint naming `--yes`.
- **Progress, warnings and notes stay on stderr and must not touch stdout.** Suppress spinners when stderr isn't a TTY. A "showing 30 of 1040" truncation note goes to stderr and exits 0, because truncating on request isn't an error.

## Compatibility rules for the output

Once `--json` ships, its output is an API, and scripts will depend on it. Human output can change freely. JSON output can't.

1. **Changes are additive only.** You can add fields. Never remove, rename, retype or repurpose an existing one. Tell consumers in the docs to ignore unknown fields, as Terraform's JSON format does.
2. **Bounded results are one document; streams are NDJSON.** A list or `get` emits a single JSON value. Anything unbounded or streaming emits one compact object per line with nothing else on stdout, so `jq` can work line by line.
3. **Pretty-print only when stdout is a TTY.** Piped output is compact. Never page `--json` output, and never color it.
4. **Use real types:**
   - Times are RFC 3339 UTC with `Z`: `"2026-10-27T15:25:16Z"`.
   - Numbers are JSON numbers: `1234567`, not `"1.2 MB"` or `"1,234"`. If you also want a display string, add a separate field for it.
   - Absent values follow one convention, either `null` or an omitted key. Pick one and document it.
5. **Put pagination cursors in the document**, e.g. `{"items":[…],"next_cursor":"…"}`. In NDJSON, where there's no envelope, put the "more available" note on stderr only.
6. **Removal needs a runway.** Deprecate first. Warn on stderr for at least one release, document it, then bump `schema_version` and ship the breaking change in a major version.
7. **Consider projections before adding more flags.** If your data is rich, kubectl's `-o json|yaml|name|jsonpath=…|custom-columns=…` is the model to grow toward. `--json` can be the first step on that path.

## Lock it in with tests

Golden-test the built binary on three channels: stdout, stderr and the exit code. Run the tests with no TTY and with `NO_COLOR` set. At minimum:

- a success case: stdout parses as JSON, stderr is empty, exit code is 0;
- each documented error `code`: stdout is empty, stderr is one valid JSON line with the expected `code`, and the exit code matches;
- a schema snapshot, so a removed or renamed field fails CI instead of breaking someone's script.

This follows `references/cli-basics.md` in the tui-design skill, mainly the *JSON / NDJSON*, *Exit codes*, *Error messages* and *Future-proofing* sections. If you tell me the language or CLI framework, I can show how to wire the error path so every failure goes through one JSON-aware formatter.
