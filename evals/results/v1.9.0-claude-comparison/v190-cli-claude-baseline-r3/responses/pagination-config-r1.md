The working directory is empty, so this is general design guidance rather than a review of your code. Send me the code and I'll apply it directly.

## Limits and pagination

**Have one user-facing knob that means "total items," not "page size."**
- `--limit N` is the total number of results across all pages. The API's page size is an implementation detail. You can expose it as `--page-size` for tuning, but most users shouldn't need it.
- Set a modest default, like 30 to 100. A bare `list` should be fast and shouldn't page through 50k records.
- `--all` (or `--limit 0`) explicitly fetches everything. Make it a separate flag so nobody gets an unbounded fetch by accident.

**Fetch lazily and stop early.**
- Page through the results and stop as soon as you have `limit` items. Don't fetch a whole page you'll throw away, if the API lets you set the page size to `min(remaining, max_page)`.
- Stream output as each page arrives, especially for `--all`, so the user sees progress and can pipe into `head`. Handle SIGPIPE/EPIPE quietly.

**Always tell the user when output was truncated. Put that message on stderr.**
```
$ tool list
ID     NAME       STATUS
...30 rows...
Showing 30 of 1,284 results. Use --limit N or --all to see more.
```
- The hint goes on **stderr** so stdout stays clean for pipes and `| wc -l` still gives the right count.
- Only print it when there really is more. Use `has_next` or a cursor if the API has one. Use the total only if the API returns it cheaply; otherwise say "30+ results".
- Skip the hint when stdout isn't a TTY, or when `--quiet` or a machine format is set.

**Give machine output the pagination state.**
- With `--json`, either output a bare array (simplest for `jq`) or an envelope like `{"items": [...], "next_cursor": "...", "truncated": true}`. Pick one, document it, and keep it stable.
- Optionally add `--cursor TOKEN` so scripts can resume where they left off without re-fetching.

**Edge cases:**
- Rate limits (429): back off and retry. With `--all`, report progress on stderr ("fetched 2,000…").
- A failure partway through: exit non-zero, and don't let partial output look complete. In JSON mode it's better to emit nothing than a truncated array that still parses.
- Validate `--limit`: reject negative values, and decide what 0 means and document it.

## Showing where config values come from

**Define the precedence once and document it.** The usual order, highest first:
1. CLI flags
2. Environment variables (`TOOL_LIMIT`)
3. Project config (`./.toolrc`)
4. User config (`~/.config/tool/config.toml`)
5. Built-in defaults

**Track where each value came from as you resolve it.** Don't just merge dicts. Store `(value, source)` pairs, for example:
```python
@dataclass
class Resolved:
    value: Any
    source: str   # "flag --limit", "env TOOL_LIMIT", "~/.config/tool/config.toml:12", "default"
```
This is cheap to do while loading config and very hard to bolt on later.

**Add a `config` subcommand that shows the sources:**
```
$ tool config list --show-origin
limit      50        env TOOL_LIMIT
endpoint   https://… ~/.config/tool/config.toml:4
format     table     default
token      ****abcd  keychain
```
- `tool config get limit --show-origin` for a single key.
- Mask secrets, and show which source they came from without printing the value.
- Support `--json` here too.
- git (`git config --show-origin`) and npm (`npm config ls -l`) work this way, so users will recognize the pattern.

**Surface the source in your own messages when it matters:**
- In errors: `invalid limit "abc" (from env TOOL_LIMIT)`. This saves a lot of "where is this coming from?" debugging.
- In `--verbose`/`--debug`, log the resolved config and its sources once at startup.
- Warn about unknown keys in config files, since a typo there otherwise fails silently.

## How the two connect

The default limit is itself a config value. When you print the truncation hint, it can help to say where the limit came from if it isn't the built-in default:

```
Showing 50 of 1,284 results (limit from ~/.config/tool/config.toml). Use --all to see more.
```

That stops users from wondering why they get 50 results when the docs say 30.

If you tell me the language and CLI framework (Click, Cobra, clap, oclif, etc.), I can sketch the actual implementation.
