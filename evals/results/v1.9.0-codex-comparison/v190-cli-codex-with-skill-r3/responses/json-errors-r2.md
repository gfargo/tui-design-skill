Treat `--json` output as a public API. Following tui-design’s CLI guidance, I recommend this failure contract:

- **stderr:** one compact JSON object followed by a newline.
- **stdout:** empty for a failed bounded command.
- **Exit status:** the same nonzero code as the equivalent human-readable failure.

```json
{"schema_version":1,"error":{"code":"permission_denied","message":"cannot write out.txt: permission denied","hint":"chmod +w out.txt"}}
```

Scripts branch on `error.code`; `message` and `hint` are human guidance and may change wording. Include what failed, why, and a useful remedy when available. Keep stack traces behind `--debug`, and avoid mixing prose, ANSI escapes, spinners, or update notices into the JSON error stream.

There’s no universal convention for JSON errors; stderr is a deliberate choice that keeps stdout reserved for results.

Compatibility rules:

| Area | Contract |
|---|---|
| Schema evolution | Add fields; never remove, rename, retype, or repurpose existing fields within a schema version. Consumers must ignore unknown fields. |
| Versioning | Version success and error schemas together. Introduce breaking changes through an explicitly documented new schema version. |
| Error codes | Keep existing codes and their meanings stable; document new codes and how consumers should handle unknown ones. |
| Values | Use JSON numbers for numbers and RFC 3339 UTC timestamps ending in `Z`. Document missing-versus-`null` semantics. |
| Framing | Bounded results use one JSON document; streaming results use NDJSON, one compact object per line. Don’t silently switch formats. |
| Presentation | Human output may evolve. Machine output remains stable; scripts must not depend on whitespace or object-key order. |

For streaming commands, records already emitted cannot be withdrawn. Document partial-result behavior: preserve valid records, emit the structured failure on stderr, and exit nonzero so callers know the stream is incomplete.

Before shipping, test **stdout, stderr, and exact exit status** for success, runtime failure, and usage errors—including without a TTY and with `NO_COLOR`.