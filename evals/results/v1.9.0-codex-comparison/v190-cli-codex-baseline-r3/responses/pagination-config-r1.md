Treat the **result limit** and **API page size** as separate controls.

- `--limit N` caps the total items returned across all pages. Keep fetching until you reach N or exhaust the results.
- `--page-size N`, if exposed, controls request size only. Changing it should not change which results users receive.
- Use a documented finite default limit. Provide `--all` for fetching every page; reject combining it with `--limit`.
- Validate limits before making requests. Define zero explicitly; preferably reject it instead of making it a surprising alias for unlimited.

Be explicit about incomplete results:

- In human output, report “Showing 100 results; more available. Use `--all` or increase `--limit`.”
- Only claim more results exist when the API provides a continuation token or you’ve checked beyond the limit. Otherwise say “Limit reached; more results may exist.”
- In JSON, include machine-readable metadata, for example:
  ```json
  {
    "items": [],
    "truncated": true,
    "next_cursor": "..."
  }
  ```
  Make the cursor usable through a corresponding `--cursor` option.
- Reaching an intentional limit is successful. An API failure midway is an error: exit nonzero and clearly identify any output as partial.
- Keep notices on stderr so stdout remains usable in pipelines. Avoid clipping field values in machine-readable output.

For configuration, provide **effective values with their sources**:

```text
$ app config explain
KEY       VALUE                  SOURCE
limit     100                    default
region    us-east-1              environment: APP_REGION
profile   staging                flag: --profile
endpoint  https://api.example    /home/me/.config/app/config.toml:8
```

Document one precedence order, such as **flags > environment > project config > user config > defaults**. Have `config explain KEY` show the winning value and overridden candidates. Offer JSON output, distinguish explicitly set values from defaults, and redact secrets in both values and provenance traces.