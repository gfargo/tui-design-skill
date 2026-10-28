Use a one-shot CLI contract: results on stdout, diagnostics on stderr, and explicit ways to retrieve more data.

**Limits and pagination**

- Give `--limit N` a finite, documented default, such as 30. It caps total returned records across API pages, not records per request.
- Offer `--paginate` to fetch all pages and `--cursor TOKEN` to resume. Document how flags interact; I recommend rejecting `--limit` together with `--paginate` as ambiguous.
- Keep API page size separate from the user’s result limit.
- When more records remain, print a note on stderr—even when stdout is redirected:

  ```text
  note: showing 30 items; pass --limit N or --paginate for more
  ```

  Say “30 of 1040” only when the API supplies a reliable total.
- Reaching the requested limit is success: exit **0**. A failed page request is an error: exit nonzero and identify any partial output.

**Truncation and output**

Distinguish omitted **records** from shortened **field values**. Human tables may shorten fields to terminal width; offer `--no-truncate`. JSON must preserve full values and expose continuation metadata:

```json
{"items":[...],"next_cursor":"opaque-token"}
```

Use `null` when exhausted. A cursor must resume after the last emitted item, including when the limit falls inside an API page. For NDJSON, keep stdout record-only and put continuation guidance on stderr.

At 80 columns, show the normal table; at 60, drop optional columns and shorten long fields. Use borderless rows without repeated status markers. Never shorten machine output. A terminal pager such as `less` is separate from API pagination: invoke it only for human output on a TTY.

**Config provenance**

Document this precedence, highest first:

```text
flags > environment > project > user > system > defaults
```

Support `--config PATH` and `MYTOOL_CONFIG`, with the flag winning. Define whether an explicitly selected file replaces normal file discovery.

Provide an effective-value view:

```text
$ mytool config list --show-origin
limit   100     env      MYTOOL_LIMIT
format  table   project  ./mytool.toml
color   auto    default  built-in
token   [redacted] env   MYTOOL_TOKEN
```

Include file paths and preferably line numbers. An optional `--explain KEY` can show overridden candidates and the winner. Redact secrets in every format, including JSON and debug output.

Verify the contract with cases for exact-limit exhaustion, remaining pages, mid-page limits, page failures, redirected output, and config overrides—asserting stdout, stderr, and exit status.