Treat **how many results users want** separately from **how the API fetches them**.

- `--limit N` caps the total items returned across pages. Fetch until you reach N or the API is exhausted.
- `--page-size N` controls API requests. Most users shouldn’t need it; changing it shouldn’t change the result limit.
- Give interactive output a reasonable default limit, such as 100. Support an explicit `--all` to fetch everything.
- Never silently truncate. Say: `Showing 100 items; more available. Use --all or --limit N.` Don’t claim a total unless the API provides one.
- If you support resuming, return a continuation token that starts after the last item actually emitted. An API cursor pointing past fetched but unprinted items would skip results.
- Treat reaching the requested limit as success. Treat an API failure partway through as a failure, and clearly identify any output as partial.

For JSON, keep notices out of stdout and expose completeness in a stable envelope:

```json
{
  "items": [],
  "has_more": true,
  "next_cursor": "..."
}
```

Document the default limit for scripted use too; don’t make JSON implicitly fetch everything.

For configuration, offer **effective values with provenance**:

```text
$ tool config explain
KEY        VALUE                    SOURCE
endpoint   https://api.example.com  user config: ~/.config/tool/config.toml:4
profile    staging                  environment: TOOL_PROFILE
limit      50                       command line: --limit
timeout    30s                      built-in default
token      [redacted]               environment: TOOL_TOKEN
```

Make precedence explicit—for example, flags → environment → project config → user config → defaults. `tool config explain limit` can show the winning value plus overridden candidates. Include file paths and line numbers where available, redact secrets, and provide a JSON format for automation.

Ideally, `tool list --explain-config` uses that same mechanism so users can inspect the values resolved for the actual command.