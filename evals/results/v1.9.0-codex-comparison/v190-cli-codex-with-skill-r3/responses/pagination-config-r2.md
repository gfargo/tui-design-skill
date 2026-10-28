Treat this as a one-shot CLI: results on **stdout**, diagnostics on **stderr**, with the same limits whether output is displayed or piped.

- Give `--limit N` a finite, documented default, such as **30 records total**, independent of API page size.
- Provide `--paginate` to fetch all pages. Define `--limit` and `--paginate` as mutually exclusive to avoid ambiguity.
- When more results exist, print an actionable stderr note—even when piped—and **exit 0**:
  ```text
  note: showing 30 items; pass --limit N or --paginate for more
  ```
  Say “30 of 1040” only when the API supplies a trustworthy total. A failed page request is an error and must exit nonzero.
- For bounded `--json`, return one document with continuation metadata:
  ```json
  {"items": [], "next_cursor": "opaque-token"}
  ```
  Support `--cursor TOKEN` to resume. For streaming NDJSON, keep stdout exclusively record objects; put continuation guidance on stderr.
- Separate **record limits** from **display truncation**. Human tables may shorten cells to fit, with `--no-truncate` available. JSON/CSV must preserve full values. Terminal paging via `$PAGER` is separate again: use it only for human output on a TTY.

For configuration, document one precedence order:

```text
flags > environment > project config > user config
      > system config > built-in defaults
```

Accept `--config PATH` and `MYTOOL_CONFIG`, with the flag winning. Specify whether an explicit file replaces normal file discovery; replacing it is a straightforward default.

Expose provenance through:

```text
$ mytool config list --show-origin
KEY     VALUE       SOURCE
limit   50          env: MYTOOL_LIMIT
format  json        /home/ann/.config/mytool/config.toml:4
color   auto        built-in default
token   [redacted]  env: MYTOOL_TOKEN
```

Show each effective value and its exact source, redact secrets, and offer an optional explanation mode for overridden candidates. Allow command context so users can inspect a particular invocation’s flags.

Keep tables borderless. At 80 columns, show key, value, and source; at 60 columns, move long sources onto an indented continuation line so paths remain readable.

Verify the contract with cases for exact-limit exhaustion, additional pages, unknown totals, page failures, piped output, JSON cursors, config precedence, and secret redaction.