Treat this as a one-shot CLI: results on stdout; notices, progress, and errors on stderr.

**Limits and pagination**

- Provide `--limit N` with a documented finite default, such as 30. It caps total returned records across API pages, not the size of each request.
- Provide `--paginate` to fetch all pages. Define combinations clearly: I recommend that an explicit `--limit N` still caps `--paginate`; without it, pagination fetches everything.
- When more results remain, print a notice to stderr, including when stdout is piped:

  ```text
  note: showing 30 of 1040 items; pass --limit N or --paginate for more
  ```

  If the total is unknown, say “showing 30 items; more available.” Don’t invent a count.
- A deliberate limit is success: exit **0**. A failed later page is incomplete work: report the failure and exit nonzero.
- For JSON, preserve full values and include continuation metadata:

  ```json
  {"items":[...],"next_cursor":"..."}
  ```

  Offer `--cursor TOKEN` to resume. The cursor must continue after the last returned item, including when a limit stops partway through an API page. For NDJSON, keep stdout record-only and put continuation information on stderr.

**Display truncation is separate**

Human tables may shorten cells to fit terminal width; provide `--no-truncate`. Never shorten field values in JSON or CSV. A terminal pager controls viewing, not API fetching: invoke it only for TTY stdout, never machine output.

At 80 columns and in a 60-column split, keep identifiers visible and shorten descriptive columns:

```text
80 columns:
ID       NAME                            STATUS
item-42  Monthly production export        ready

60 columns:
ID       NAME                     STATUS
item-42  Monthly production exp…   ready
```

Use no borders or repeated row markers; one header and one truncation notice are sufficient.

**Configuration provenance**

Document precedence, highest first:

```text
flags > environment > project > user > system > defaults
```

Support `--config PATH` and `MYTOOL_CONFIG`, with the flag winning. Document whether an explicit file replaces normal file discovery; I recommend that it does, while flags and environment still override its values.

Provide an inspection command:

```text
$ mytool config list --show-origin
limit   30      default
format  json    /home/ann/.config/mytool/config.toml:4
color   never   env:MYTOOL_COLOR
```

Show each effective value and its exact source. An optional `--explain KEY` can show overridden candidates and why the winner won. Redact secrets in every output format while retaining their source. At narrow widths, render each setting as a small multiline block so paths remain readable.

Verify these contracts with tests covering stdout, stderr, and exit status—especially piped output, exact page boundaries, mid-page limits, unknown totals, later-page failures, and conflicting config sources.