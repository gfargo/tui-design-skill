With `--json`, make failures **one compact JSON line on stderr**, leave stdout empty, and preserve the same nonzero exit status as the human-readable failure. There’s no universal convention; this keeps stdout reserved for results.

```json
{"schema_version":1,"error":{"code":"permission_denied","message":"cannot write out.txt: permission denied","hint":"chmod +w out.txt"}}
```

Use a stable `error.code` for scripts to branch on. Keep `message` readable and `hint` actionable; consumers shouldn’t parse either. Omit stack traces unless `--debug` is enabled. Keep color, spinners, and human prose out of the JSON.

Treat the output as a public API:

- **Changes within a schema version are additive:** never remove, rename, retype, or repurpose existing fields. Consumers must ignore unknown fields.
- **Version success and error schemas together.** Breaking changes require an explicit new schema version and a documented migration/deprecation path.
- **Keep machine output stable.** Human-readable formatting can evolve independently.
- **Use consistent data types:** timestamps in RFC 3339 UTC (`2026-10-27T15:25:16Z`); numbers as JSON numbers, without units or thousands separators.
- **Bounded results:** one JSON document on stdout. **Streaming results:** NDJSON, one compact object per line. Document that a stream may emit results before failing; preserve those records and exit nonzero.
- Never page machine output. Pretty-print bounded JSON only on a TTY.

Before shipping, test stdout, stderr, and the exact exit status for success, usage errors, and operational failures—including without a TTY and under `NO_COLOR`.