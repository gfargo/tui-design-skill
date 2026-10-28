Here's a set of conventions that work well and match what tools like `gh`, `kubectl`, and `terraform` do.

## Failures under `--json`

**1. stdout always holds exactly one valid JSON document, even when the command fails.** Scripts will run `mycli foo --json | jq ...`, so a failure should still produce parseable output on stdout:

```json
{
  "ok": false,
  "error": {
    "code": "config_not_found",
    "message": "No config file at ~/.mycli/config.toml",
    "details": { "path": "/Users/x/.mycli/config.toml" }
  }
}
```

- `code` is a stable, machine-readable string (snake_case). Scripts branch on this. Treat it as part of your API.
- `message` is for humans. Its wording can change at any time, so tell users not to parse it.
- `details` is optional, holds structured context, and can differ per error code.

**2. Exit codes still matter and mean the same thing as without `--json`.** Non-zero on failure. If you have distinct codes (e.g. 1 = general error, 2 = usage error), keep them. Plenty of callers check `$?` and never read the body.

**3. stderr is free-form.** Progress bars, warnings, and debug logs go to stderr, never stdout. Some CLIs also print the human-readable error to stderr. That's fine as long as stdout stays clean.

**4. Fail as JSON as early as you can.** If the arguments can be parsed far enough to see `--json`, usage errors should also come out as JSON. Crashes before that point (or panics) may not, and that's acceptable, but wrap your top-level handler so unexpected exceptions become `{"ok": false, "error": {"code": "internal_error", ...}}`.

**5. Partial success needs a deliberate design.** For batch operations, return per-item results instead of failing the whole document:

```json
{ "ok": false, "results": [ {"id": "a", "ok": true}, {"id": "b", "ok": false, "error": {...}} ] }
```

Document which exit code that case returns.

**Success shape:** pick one of these and keep it everywhere. Either use `{"ok": true, "data": ...}` as an envelope, or emit the bare data on success and use the presence of the `error` key to signal failure. The envelope is easier to evolve. Bare data is nicer with `jq`. I'd use the envelope for a new CLI.

## Compatibility rules

Once you ship `--json`, its output is a public API. Version it like one.

**Allowed (non-breaking):**
- Adding new fields to objects
- Adding new error `code` values
- Adding new values to enums, as long as you've documented that consumers must tolerate unknown values
- Changing the `message` text
- Changing key order or whitespace

**Breaking (needs a major version or a new schema version):**
- Removing or renaming a field
- Changing a field's type (`"3"` → `3`, scalar → array, object → null)
- Changing what a field means or its units (seconds → ms)
- Making a field that was always present optional or nullable
- Changing or removing an existing error `code`
- Changing exit code meanings
- Changing the top-level shape (bare value → envelope)

**Practices that make this sustainable:**
- **Document the contract:** "Consumers must ignore unknown fields and unknown enum values. `message` is not stable." That gives you room to add things later.
- **Be explicit about nulls:** decide whether a missing value is an omitted key or `null`, and do it the same way everywhere.
- **Use stable formats:** ISO-8601 UTC timestamps, numbers as numbers, IDs as strings (so large ints don't lose precision in JS).
- **Don't let JSON depend on terminal state:** no color codes, no locale-dependent formatting, no truncation based on terminal width.
- **Consider a schema version** (`"schema_version": 1`) or a `--json-version` flag if you expect real churn. Most CLIs never need one if they stick to "add-only".
- **Snapshot-test the JSON output** for each command and each error code, so an accidental rename shows up in CI.
- **Streaming/large lists:** if you'll ever stream results, decide now between one JSON document and NDJSON (one object per line, probably as a separate `--jsonl` flag). Switching later is a breaking change.

If you share the CLI's language or framework, or point me at the code, I can sketch the top-level error handler and the envelope types.
