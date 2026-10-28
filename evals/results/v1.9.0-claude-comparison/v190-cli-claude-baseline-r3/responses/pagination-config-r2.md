The working directory is empty, so this is general guidance rather than a review of your code. Here's the design I'd recommend.

## Limits and pagination

**1. Use one `--limit` flag that counts items, not pages.**
Users care about how many results they get. Pagination is an API detail. Fetch pages internally until you have `limit` items or the API runs out.

```
mycli list --limit 50      # exactly up to 50 items, however many pages that takes
mycli list --all           # fetch everything (explicit opt-in)
```

- Pick a sensible default, like 30 to 100. Never fetch everything by default, because unbounded API calls are slow and can hit rate limits.
- `--limit 0` or `--all` means no limit. Choose one and document it. `--all` is easier to discover.
- Keep `--page-size` (the per-request size) separate and hidden or advanced. Default it to the API's maximum so you make fewer round trips. Stop fetching as soon as you reach `limit`, and trim the last page.

**2. Always tell users when output was truncated, on stderr.**
This is the most commonly missed piece. If more results exist, print a hint:

```
Showing 50 of 1,284 results. Use --limit N or --all to see more.
```

- Send it to **stderr** so `mycli list | jq` and `> file` stay clean.
- If the API doesn't return a total, say "Showing first 50 results (more available)". You know more exist because there's a next cursor.
- Hide the hint when stdout isn't a TTY, or keep it on stderr either way. Hide it with `--quiet`.
- In `--json` output, put truncation in the payload so scripts can detect it:
  ```json
  { "items": [...], "truncated": true, "next_cursor": "abc123" }
  ```
  Alternatively, use NDJSON with no wrapper and rely on the stderr hint plus the exit code. Pick one approach and stay consistent.

**3. Exit code 0 for a truncated success.** Truncation isn't an error. Don't make scripts treat it as one.

**4. Optional: expose the cursor for resumable scripting.**
`--cursor <token>` together with `next_cursor` in the JSON output lets power users page manually without you building interactive paging.

**5. Stream when you can.** For table or line output, print each page as it arrives instead of buffering everything. It feels much faster with `--all`. Column widths make this harder for tables, so buffering tables and streaming NDJSON is a reasonable split.

**6. Handle interruption and rate limits.** On Ctrl-C, print what you have and exit. On 429 responses, back off and retry with a short stderr notice rather than failing halfway through.

## Showing where config values come from

**1. Document one precedence order and stick to it.**
Highest to lowest:
```
flag  >  env var  >  project config (./.mycli.toml)  >  user config (~/.config/mycli/config.toml)  >  built-in default
```

**2. Track the source with each value as you resolve it.**
Don't merge everything into a flat dict and lose the origin. Store `(value, source)` pairs:

```python
@dataclass
class Resolved:
    value: Any
    source: str   # "flag --limit", "env MYCLI_LIMIT", "~/.config/mycli/config.toml:12", "default"
```

Including the file path and line number makes this much more useful for debugging.

**3. Add a `config` command that shows the resolved values with their sources:**

```
$ mycli config list --show-origin
KEY         VALUE                     SOURCE
limit       50                        env MYCLI_LIMIT
api_url     https://api.example.com   ~/.config/mycli/config.toml:3
page_size   100                       default
token       ****f3a9                  keychain
```

- `mycli config get limit --show-origin` shows a single key. This follows git's `git config --show-origin` convention, which many users already know.
- **Redact secrets** by default, showing only the last 4 characters. Add `--show-secrets` if you really need it.
- Support `--json` here too.
- Optionally list *overridden* values, e.g. "limit = 100 in config.toml (overridden by env)". This answers the common "why isn't my config file working?" question.

**4. Show where config files live and which ones exist:**
```
$ mycli config path
~/.config/mycli/config.toml   (exists)
./.mycli.toml                 (not found)
```

**5. Use `--verbose` / `--debug` for runtime visibility.** At startup, log resolved values that differ from their defaults, along with their sources, to stderr. When someone files a bug, their `--debug` output then tells you how the CLI was configured.

## How the two connect

`limit` is a config value too. A user who sets `limit = 500` in their config file and then sees "Showing 500 of 1,284" can run `mycli config get limit --show-origin` to find out where that 500 came from. You can also add the source to the truncation hint when the limit isn't the default:

```
Showing 500 of 1,284 results (limit from ~/.config/mycli/config.toml). Use --all to see more.
```

If you share your language, CLI framework (Click, Cobra, clap, oclif, etc.), and the API's pagination style (cursor, offset, or link headers), I can sketch the actual fetch loop and config resolver.
