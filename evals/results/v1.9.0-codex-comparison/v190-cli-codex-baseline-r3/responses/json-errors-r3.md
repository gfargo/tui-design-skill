Treat `--json` as a machine-readable API, including when the command fails.

A useful failure shape is:

```json
{
  "ok": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Project 'demo' was not found.",
    "details": {
      "resource": "project",
      "name": "demo"
    }
  }
}
```

Use these rules:

- **Keep the exit status meaningful.** Return nonzero on failure; JSON does not replace exit codes.
- **Choose one output contract.** A good default is one JSON object on stdout for both success and failure. Reserve stderr for optional diagnostics, and keep stdout free of progress bars, banners, and logs. If you choose stderr for JSON errors instead, document that consistently.
- **Emit valid JSON only.** No colors, comments, or text before or after the document. End it with a newline. For streaming output, explicitly define a separate format such as NDJSON.
- **Use stable error codes.** Scripts should branch on `error.code`, never parse `message`. Messages can improve over time.
- **Handle early failures too.** Invalid arguments, configuration errors, and authentication failures should follow the JSON contract whenever `--json` is recognized.
- **Protect sensitive data.** Don’t include credentials, raw responses containing secrets, or stack traces by default.

For compatibility, define the contract explicitly:

| Change | Compatibility |
|---|---|
| Add an optional object field | Usually compatible; consumers must ignore unknown fields |
| Change wording in a human-readable message | Compatible if documented as unstable |
| Remove or rename a field | Breaking |
| Change a field’s type, meaning, or nullability | Breaking |
| Change an error code or exit-code meaning | Breaking |
| Change stdout/stderr placement or document framing | Breaking |
| Add an enum value or error code | Compatible only if consumers are required to handle unknown values |
| Change array ordering | Breaking if ordering was promised |

Document which fields are required, when fields are absent versus `null`, and any ordering guarantees. Publish examples or a schema, and test the contract.

If you expect breaking changes, provide an explicit output version such as `--json-version=1`. A `"schema_version": 1` field helps identify output, but alone doesn’t let existing consumers request the old format.