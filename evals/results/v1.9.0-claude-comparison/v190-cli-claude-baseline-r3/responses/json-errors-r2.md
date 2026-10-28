I didn't find any code in the working directory, so this is general guidance. Share the CLI and I can apply it to your code.

## Failures under `--json`

**1. Stdout carries the result, stderr carries diagnostics, and the exit code is the main signal.**
- On success: write exactly one JSON document to stdout and exit 0.
- On failure: exit non-zero. Callers check `$?` before they parse anything, so never exit 0 with an error object.
- Never mix human text into stdout. Progress messages, warnings, spinners and deprecation notices all go to stderr, or are left out. A single stray line breaks `jq`.

**2. Still write a structured error to stdout on failure.** Scripts usually capture only stdout, so put the error in a stable envelope there:

```json
{
  "ok": false,
  "error": {
    "code": "config_not_found",
    "message": "No config file at ./app.toml",
    "details": { "path": "./app.toml" }
  }
}
```

- **`code`** is a stable, machine-matchable identifier (snake_case string, not a number). It's part of your contract.
- **`message`** is human-readable and can change at any time. Tell users not to match on it.
- **`details`** is optional context specific to each code.
- On success, use `{"ok": true, "data": ...}`, or just return the bare result object. Pick one and keep it. An envelope costs some verbosity and makes `ok` checks easy.

You can also print a short human message to stderr, which helps someone running the command by hand.

**3. Document distinct exit codes:** for example 0 success, 1 general/runtime failure, 2 usage error (bad flags), and more only if callers really need to branch on them. Don't encode much detail in exit codes; that's what `error.code` is for.

**4. Usage errors need care.** If the flags can't be parsed, you may not know whether `--json` was set. Do a best-effort pre-scan of argv for `--json`, and emit the JSON error if you find it.

**5. Partial failures** (batch operations): exit non-zero, and report per-item results so callers can see what succeeded:

```json
{ "ok": false, "results": [ {"id": "a", "ok": true}, {"id": "b", "ok": false, "error": {...}} ] }
```

**6. Panics and crashes:** add a top-level handler that turns unexpected errors into `{"ok": false, "error": {"code": "internal", ...}}` instead of printing a stack trace on stdout. Send the trace to stderr.

**7. Streaming output:** if you emit multiple records, use NDJSON (one object per line), and make the last line, or an error line, distinguishable, e.g. `{"type": "error", ...}`.

## Compatibility rules

Once `--json` ships, treat its output as a public API.

**Safe (non-breaking) changes:**
- Adding new fields to objects.
- Adding new error codes, as long as callers are told to expect unknown codes.
- Adding new enum values, only if you documented that enums are open. Otherwise treat it as breaking.
- Changing `message` text.

**Breaking changes (need a major version or a new format version):**
- Removing or renaming fields.
- Changing a field's type (`"5"` → `5`, scalar → array, object → null).
- Changing what a field means or its units (seconds → ms).
- Changing or removing an existing error code.
- Changing exit-code meanings.
- Changing the top-level shape (bare array → envelope).

**Practices that keep you out of trouble:**
- **Be consistent about absent values:** decide whether missing means `null` or an omitted key, and apply it everywhere.
- **Use stable types:** timestamps in RFC 3339 UTC, durations as integers with the unit in the name (`duration_ms`), and IDs as strings even when they look numeric.
- **Keep it deterministic:** stable key order and sorted lists where order isn't meaningful. This makes diffs and tests easier.
- **Don't let human formatting leak in:** no colors, truncation, locale-formatted numbers or relative times ("3 min ago"). Ignore `NO_COLOR` and TTY detection in JSON mode, because the output should be identical either way.
- **Version the schema:** for example `"schema_version": 1` in the envelope, or `--json=v2` / `--format json-v2` when you need to break. Support the old version for a deprecation period.
- **Tell consumers to tolerate unknown fields.** That's the only way additive changes stay non-breaking.
- **Publish the contract:** a JSON Schema per command plus a list of error codes. Add golden-file tests that fail when the output shape changes, so breaking changes are deliberate.
- **Mark what's unstable:** if some commands or fields aren't ready, say so explicitly (e.g. an `experimental` section in the docs) rather than leaving it implicit.

**Quick rule of thumb:** a script written against today's output should keep working after any minor release. That means it can still parse stdout, branch on exit code and `error.code`, and read every field it read before.
