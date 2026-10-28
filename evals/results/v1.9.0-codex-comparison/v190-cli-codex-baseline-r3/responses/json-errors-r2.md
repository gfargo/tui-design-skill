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

- **Exit nonzero on failure.** JSON doesn’t replace exit status. Document any distinct exit codes.
- **Emit exactly one JSON document to stdout**, for both success and failure. No banners, progress bars, ANSI colors, or trailing explanatory text. If you need streaming, define a separate NDJSON contract.
- **Keep stderr for optional diagnostics.** Consumers should be able to understand a normal failure from the JSON alone. Don’t expose stack traces or secrets by default.
- **Cover predictable failures consistently**, including validation, authentication, and argument errors whenever `--json` can be recognized. Document that crashes or external termination may prevent valid JSON.
- **Make `error.code` stable and machine-readable.** Treat `message` as human-readable text that may change; consumers shouldn’t parse it.
- **Define partial success explicitly.** Batch commands should report per-item outcomes and have a documented exit-status policy.

For compatibility, promise that within a supported schema version:

| Change | Compatibility rule |
|---|---|
| Add an optional object field | Generally safe; consumers must ignore unknown fields |
| Remove or rename a field | Breaking |
| Change a field’s type, meaning, or nullability | Breaking |
| Change human-readable messages | Safe if documented as non-contractual |
| Add an error code or enum value | Safe only if consumers are required to handle unknown values |
| Change ordering | Safe only where ordering is explicitly unspecified |
| Change exit-status behavior | Potentially breaking |

Distinguish missing fields from `null`, and specify which fields are always present. Avoid timestamps, request IDs, or other variable metadata unless they serve a purpose.

If you expect incompatible changes, introduce a schema version or an explicit output-version selector. Keep that separate from the CLI’s release version.