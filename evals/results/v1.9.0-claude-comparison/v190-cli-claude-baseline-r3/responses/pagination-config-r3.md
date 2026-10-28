The working directory is empty, so this is general guidance rather than a review of your code. Share the command when you have it and I can apply it.

## Limits and pagination

**Pick a finite default and fetch pages until you reach it.**
- Use something like `--limit 30` by default. An unbounded default turns `mycli list` into a slow, rate-limit-burning call on large accounts.
- Treat `--limit` as the number of **items**, not pages. Fetch pages internally until you have that many, then stop. Request `min(remaining, max_page_size)` per page so you don't over-fetch.
- Give users an explicit opt-in for everything, such as `--all` or `--limit 0`. Don't make them guess a huge number.
- Keep `--page-size` separate and optional. Most users never need it.

**Make truncation visible, on stderr, only when something was actually cut off.**
```
$ mycli list
NAME        STATUS   UPDATED
alpha       active   2h ago
...
Showing 30 of 1,284 results. Use --limit N or --all to see more.
```
- Put the notice on **stderr** so `mycli list | wc -l` and pipes into other tools stay clean.
- Say "30 of 1,284" if the API gives a total. If not, say "Showing first 30 results (more available)". Only claim more results exist when the API returned a next cursor or the last page was full.
- Print nothing extra when the result wasn't truncated.
- Hide the notice for `--quiet` and when stderr isn't a TTY, if that's your convention.

**Structured output needs truncation info too.** With `--json`, a stderr notice is easy to miss, so put it in the output:
```json
{ "items": [...], "truncated": true, "next_cursor": "eyJ...", "total": 1284 }
```
Alternatively, keep a bare array by default and add an envelope flag. Exposing the cursor (and accepting it via `--cursor`) lets scripts resume where they stopped.

**Edge cases:**
- **Rate limits (429):** respect `Retry-After` and back off. With `--all`, show progress on stderr for long fetches ("Fetched 400/1284…").
- **Partial failure mid-pagination:** print what you got, report the error and the resume cursor, and exit non-zero.
- **Ordering:** pick a stable sort so `--limit` returns the same items each time.
- **Streaming output:** for big `--all` runs, print rows as pages arrive. This doesn't work with aligned table columns, so stream for `--json`/NDJSON and buffer for tables.

## Showing where config values come from

**Use one fixed precedence order and document it:**
```
flags > environment variables > project config (./.mycli.toml) > user config (~/.config/mycli/config.toml) > built-in defaults
```

**Track the source of each value as you load it.** Store `(value, source)` pairs, not just the merged result, so you can explain any value without recomputing.

**Add a command that shows each value and its source:**
```
$ mycli config list --show-origin
KEY          VALUE                 SOURCE
limit        100                   env MYCLI_LIMIT
api_url      https://api.example   ~/.config/mycli/config.toml:3
output       table                 default
token        ****a91f              keychain
```
- Include file path and line number where you can. Git's `git config --show-origin` is a good model.
- Add a per-key form, `mycli config get limit --show-origin`. Consider a verbose mode that lists every layer that set the key and marks which one won. That answers "I set it in my config file, why isn't it working?"
- **Mask secrets** by default, with an explicit `--reveal` if you need one.
- Support `--json` here too, for scripted debugging.

**Connect the two features.** When a limit came from somewhere other than the default, the truncation notice can say so:
```
Showing 100 of 1,284 results (limit from MYCLI_LIMIT). Use --all to see more.
```
Without this, users often don't realize an env var or config file is capping their output.

If you tell me your language and CLI framework (e.g. Go/cobra, Python/click, Rust/clap, Node/oclif), I can sketch the pagination loop and the source-tracking config loader for your setup.
