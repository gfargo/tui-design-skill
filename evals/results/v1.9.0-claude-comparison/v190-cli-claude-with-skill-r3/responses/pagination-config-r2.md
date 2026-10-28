**Recommendation:** use a bounded default with `--limit`, add `--paginate` to fetch everything, and print a note on stderr whenever results were cut off. Exit 0 in that case, because returning fewer results on request isn't an error. Add a `config list --show-origin` command that prints each effective value next to the layer it came from.

## 1. Limits and pagination

**Pick one model and document it.** Two models are common:

| Model | Example | Behavior |
|---|---|---|
| Bounded by default | `gh` (`--limit 30`) | Fast and predictable, but can silently hide rows |
| Fetch everything by default | AWS CLI (`--max-items` + `NextToken`) | Complete, but slow or expensive on large sets |

For most tools I'd choose **bounded by default**, with a finite default like 30–100 and these flags:

- `--limit N` caps the total number of items returned, across API pages. Don't expose the API's page size as the user-facing number.
- `--paginate` (or `--all`) follows the cursor until the API runs out.
- `--cursor TOKEN` (optional) resumes where a previous run stopped.

**Never truncate silently.** `gh` does this when output is piped, and it causes real bugs in scripts. When the limit cuts results off, say so on **stderr** and include the flag that gets the rest:

```
$ mytool list --limit 30 > items.txt
note: showing 30 of 1040 items; pass --limit N or --paginate for more
$ echo $?
0
```

- The note goes to stderr, so `items.txt` contains only data.
- The exit code is 0, because the user asked for at most 30.
- If the API doesn't return a total, say `showing first 30 items; more available` rather than inventing a count.
- `-q` suppresses the note.

**Machine output:**

- With `--json` (one document), put the cursor in the document so scripts can continue without parsing stderr:
  ```json
  {"items":[…],"next_cursor":"eyJvZmZzZXQiOjMwfQ"}
  ```
  Use `"next_cursor": null` when there's nothing more. Never remove or rename these fields later; only add new ones.
- With NDJSON (one object per line, for streaming or `--paginate`), stdout holds nothing but item lines. The "more available" message goes only in the stderr note.
- With `--paginate`, write items to stdout as each page arrives rather than buffering everything. Show page progress on stderr, and only when stderr is a TTY.

**Failure partway through `--paginate`:** if page 7 fails, the items already printed stay printed. Exit non-zero and put the error on stderr, with a cursor to resume from if you have one. Unlike a limit you asked for, an incomplete fetch *is* an error.

## 2. Truncating column values

This is a separate kind of truncation: long values inside the table.

- Show one record per line with no ASCII borders, so `wc -l` and `grep` still work.
- Truncate cells to the terminal width with `…`, and offer `--no-truncate` to turn it off.
- Measure display width in terminal cells, not bytes or string length. CJK characters and emoji take two cells.
- When stdout is not a TTY, don't truncate to a width at all. Scripts need the full values.
- Also offer `--columns`, `--json`, and `--csv`.

At 80 columns:
```
ID       NAME                         STATUS    UPDATED
a81f3c   billing-service-prod         running   2026-10-27T14:02:11Z
c09e12   search-indexer-backfill-…    failed    2026-10-27T13:55:40Z
```
At 60 columns, cut low-value columns before squeezing the name down to nothing:
```
ID       NAME                         STATUS
a81f3c   billing-service-prod         running
c09e12   search-indexer-backfill-…    failed
```

## 3. Showing where config values come from

**Precedence, highest first:** flags → env vars (`MYTOOL_*`) → project config (`./mytool.toml`) → user config (`$XDG_CONFIG_HOME/mytool/config.toml`, falling back to `~/.config/mytool/`) → system config (`/etc/mytool/`) → built-in defaults. Also accept `--config PATH` and `MYTOOL_CONFIG`; the flag beats the env var.

**Show the origin**, the way `git config --show-origin`, `npm config list -l`, and `aws configure list` do:

```
$ mytool config list --show-origin
user     ~/.config/mytool/config.toml   limit  = 100
env      MYTOOL_LIMIT                   limit  = 50       (wins)
project  ./mytool.toml                  format = "json"
default                                 color  = "auto"
default                                 token  = ********
```

- List overridden values too, and mark which one wins. "Why is my setting ignored?" is the question this command exists to answer.
- Always redact secrets. Better still, keep tokens out of flags and config entirely and use a credential store or env var.
- Offer `--json` for this command as well (`{"key":"limit","value":50,"source":"env","origin":"MYTOOL_LIMIT","overridden":[…]}`).
- Optionally add `mytool config get limit --show-origin` for a single key.

These two features meet at `--limit`: if a user sets `limit = 500` in config and gets 50 results, `--show-origin` should immediately show `MYTOOL_LIMIT=50` in their environment overriding it.

## Tests to pin down

Write golden tests that check stdout, stderr, and the exit code together, running without a TTY and under `NO_COLOR`:
- Truncated run: data only on stdout, note on stderr, exit 0.
- `--json` returns `next_cursor`, and it's `null` on the last page.
- `--paginate` with a failure on a middle page: exit non-zero, already-printed items kept.
- Config precedence for every layer, including a lower layer that is overridden.
