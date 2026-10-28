Treat `--json` as a public API. Following tui-design’s CLI guidance, I recommend this failure contract:

- **stdout:** empty for a failed bounded command.
- **stderr:** one compact JSON object followed by a newline.
- **Exit status:** the same nonzero code as the equivalent human-readable failure.
- **No extra decoration:** no ANSI colors, spinner output, prose prefixes, or default stack traces.

For example, stderr could contain:

```json
{"schema_version":1,"error":{"code":"permission_denied","message":"cannot write out.txt: permission denied","hint":"choose a writable output path"}}
```

Scripts should branch on `error.code`; `message` and `hint` are human-facing text whose wording can improve. Keep stack traces behind `--debug`, and document how debug output interacts with structured errors. Structured error placement has no universal convention, so clearly document your stderr choice.

The compatibility rules should be:

| Area | Contract |
|---|---|
| Fields | Additive changes only within a schema version. Never remove, rename, retype, or repurpose existing fields. |
| Consumers | Ignore unknown fields; don’t depend on object key order or whitespace. |
| Error codes | Stable identifiers with stable meanings. |
| Versioning | Version errors together with success output. Introduce incompatible changes through an explicit new schema version. |
| Values | Use JSON numbers for numeric data and RFC 3339 UTC timestamps, such as `2026-10-27T15:25:16Z`. Document null versus omitted fields. |
| Framing | Bounded results use one JSON document. Streaming results use NDJSON: one compact object per line. Keep that choice stable. |

For streaming failures, already-emitted records cannot be withdrawn: retain them, emit the structured error on stderr, and exit nonzero. Document that a successful exit is required to consider the stream complete.

Before shipping, test **stdout, stderr, and exact exit status** for success, usage errors, runtime failures, and partial streams—including without a TTY and with `NO_COLOR`. Human-readable output can evolve; machine-readable output needs this compatibility commitment.