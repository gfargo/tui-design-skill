Treat **result limits, API page size, and display truncation as separate controls**.

- `--limit N` caps the total number of results returned across pages. Fetch additional pages until you reach N or exhaust the results.
- `--page-size N` controls each API request, not the total. Usually this can remain an implementation detail.
- Use a documented default limit, such as 100, and provide `--all` to fetch every page. Reject conflicting `--all` and `--limit` flags.
- Preserve the API’s ordering across pages. If fetching a later page fails, report an error and exit nonzero; don’t silently present partial results as complete.

When results are capped, make that visible:

```text
Showing 100 results; more are available. Use --all or --limit N.
```

Only claim more results exist when the API confirms it through a cursor, count, or additional item. Otherwise say “Limit reached; more results may be available.” A deliberate limit should normally exit successfully.

For machine output, keep notices off stdout. Either use a documented JSON envelope with pagination metadata, or send notices to stderr if stdout is a plain array or JSON Lines. Include a continuation cursor if users need to resume fetching. Display shortening—such as ellipsized table cells—should never shorten values in structured output.

For configuration, provide an effective-value view with provenance:

```text
$ tool config list --show-source
KEY       VALUE                     SOURCE
endpoint  https://api.example.com   default
region    us-east-1                 ~/.config/tool/config.toml:8
profile   staging                   environment: TOOL_PROFILE
timeout   30s                       flag: --timeout
token     [REDACTED]                 environment: TOOL_TOKEN
```

Document one precedence order, for example **flags → environment → project config → user config → defaults**. Add `tool config explain <key>` to show the winning value and overridden sources. Show actual file paths and profile names, and redact secrets consistently—including in diagnostic output.