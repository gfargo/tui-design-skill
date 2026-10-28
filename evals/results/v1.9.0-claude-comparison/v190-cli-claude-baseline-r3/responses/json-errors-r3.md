Here's how I'd set it up. I'm treating this as general advice, not tied to your codebase.

## Failures under `--json`

**1. Write one JSON document to stdout, whether the command succeeds or fails.** A script should be able to read and parse stdout every time without first checking which case it's in. Free-form diagnostics like warnings, progress and debug logs go to stderr.

**2. Make the exit code the source of truth.** Exit 0 means success. Anything else means failure, even though stdout still holds valid JSON. Document a small set of exit codes:
- `1` for a general failure
- `2` for usage errors, like a bad flag or missing argument
- a few others only if callers really need to branch on them (e.g., auth or not-found)

**3. Use a consistent error envelope:**
```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Project 'foo' does not exist",
    "details": { "project": "foo" }
  }
}
```
- `code` is a stable, machine-readable string that callers can branch on.
- `message` is for humans. Say in your docs that its wording can change.
- `details` is optional structured context.

**4. Handle partial failures explicitly.** For batch or multi-item commands, report a status for each item and exit non-zero if any item failed:
```json
{ "results": [ { "id": "a", "ok": true }, { "id": "b", "ok": false, "error": { "code": "...", "message": "..." } } ] }
```

**5. Keep stdout clean.** With `--json` set, never write ANSI colors, spinners, prompts or banners to stdout. Interactive prompts should either fail with an error code like `confirmation_required` or need a `--yes` flag.

**6. Catch errors that happen early.** Argument-parsing failures and uncaught exceptions should also produce the JSON envelope whenever `--json` appears in argv. This is the case people most often miss.

**7. Use NDJSON for streaming or long-running commands.** Emit one object per line and make the final line a summary or error record.

## Compatibility rules

These changes are safe in any release:
- Adding new fields
- Adding new error codes
- Adding new values to enums, as long as you've documented that callers must tolerate unknown values
- Adding new commands

These are breaking changes:
- Removing or renaming a field
- Changing a field's type, e.g., number to string or object to array
- Changing what a field means or its units, e.g., seconds to milliseconds
- Switching between `null` and omitting a field, unless you've documented that the two are equivalent
- Changing exit-code meanings or existing error `code`s
- Changing between a single document and NDJSON

**Conventions to fix from day one:**
- Timestamps are RFC 3339 / ISO 8601 in UTC.
- IDs are always strings.
- Durations include their unit in the field name, e.g., `duration_ms`.
- Field order isn't guaranteed.
- Consumers must ignore fields they don't recognize.

**Versioning:**
- Treat the JSON schema as part of your public API under semver, so a breaking change means a major version bump.
- If you expect it to evolve a lot, you could add a top-level `"schema_version": 1` or accept `--json=v2`. That lets you ship a new format alongside the old one.
- Deprecate before removing: keep the old field, document it as deprecated, and remove it in the next major version.

**Document what isn't covered.** Human-readable output (without `--json`), `message` text and stderr content are explicitly *not* stable.

**Enforce it in CI.** Publish a JSON Schema for each command's output and run snapshot or contract tests against it, covering error cases too. Tests catch accidental breaking changes more reliably than review does.

If you tell me the language or CLI framework you're using, I can sketch the error-handling wrapper that guarantees the envelope even for early failures.
