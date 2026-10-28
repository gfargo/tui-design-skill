## Short answer

- **Row limits:** use a finite default `--limit` (30 or so) plus `--paginate` to fetch everything. When results get cut off, print a note on **stderr** that says so and names the flag that gets the rest. Exit **0**, because returning the number of rows the user asked for isn't an error.
- **Config sources:** add `mytool config list --show-origin`. It prints each effective value, the layer it came from, and which layer won, with secrets redacted.

The two are linked: `limit` is itself a config value. When someone asks "why am I only getting 50 rows?", `config list --show-origin` answers it.

---

## 1. Limits and pagination

### Flags

| Flag | Behavior |
|---|---|
| `--limit N` | Return at most N items. Default 30. Also settable in config or `MYTOOL_LIMIT`. |
| `--paginate` | Follow cursors until the API runs out of pages. Overrides `--limit`. |
| `--cursor TOKEN` (optional) | Resume from a cursor you printed earlier. Useful for scripts that page by hand. |

Pick **one** default design and document it. There are two real precedents:
- **gh:** bounded by default (`--limit 30`). Its flaw is that it truncates silently when piped. Don't copy that part.
- **AWS CLI:** fetches every page by default. `--max-items` caps the count and adds a `NextToken`.

For an interactive tool I'd go with bounded-by-default. Users get a fast first response, and nobody accidentally makes 200 API calls.

### Say when you truncated, even when piped

```
$ mytool list --limit 30 > items.txt
note: showing 30 of 1040 items; pass --limit N or --paginate for more
$ echo $?
0
```

Rules:
- The note goes to **stderr**, so `items.txt` contains only data and `wc -l` stays accurate.
- Print it **whether or not stdout is a TTY**. Piping is exactly when a silent cutoff does the most damage.
- If the API doesn't return a total, say `showing first 30 items; more available — pass --paginate`. Don't invent a count.
- `-q` suppresses it, since it's non-essential diagnostic output. Errors still print.
- Exit 0. Save non-zero codes for real failures (auth, network, a page failing mid-`--paginate`).

### Machine output

- **`--json` (a single bounded document):** put the cursor in the document so scripts can continue without parsing stderr:
  ```json
  {"items":[…],"next_cursor":"eyJvZmYiOjMwfQ","total":1040}
  ```
  Leave `next_cursor` null or omit it when there are no more pages. Only add fields to this schema; never rename or remove them.
- **NDJSON or streaming** (e.g. `--json` with `--paginate`): stdout has exactly one object per line and nothing else. The truncation note goes only to stderr.
- Never send `--json` output through the pager.

### Long runs with `--paginate`

- Stream each page to stdout as it arrives instead of buffering all 1040 items.
- After about 150 ms, show progress on stderr, and only if stderr is a TTY: `fetching page 7… (210 items)`.
- If page 12 fails, the 330 items already written stay on stdout. Print the error and the resume cursor on stderr, then exit non-zero:
  ```
  error: page 12 failed: 503 Service Unavailable
  hint: resume with --cursor eyJvZmYiOjMzMH0 --paginate
  ```
- Ctrl+C exits 130 and doesn't leave half-written lines.

### Width truncation is separate from row truncation

The human table also truncates cells to fit the terminal. Treat that as its own setting with its own off switch:

- Truncate only on a TTY. When piped, print full values.
- Measure **terminal cell width**, not string length. CJK and emoji take two cells.
- Provide `--no-truncate`, `--columns`, and `--no-headers`. Don't draw ASCII borders.

Here's 80 columns versus a 60-column tmux split. The least important column drops out first, then the widest one shrinks:

```
80 cols
NAME                    STATUS    OWNER        UPDATED
billing-api             running   ann          2026-10-27T14:02Z
search-indexer-backfi…  failed    platform     2026-10-26T09:41Z

60 cols  (OWNER dropped, NAME shrunk)
NAME              STATUS    UPDATED
billing-api       running   2026-10-27T14:02Z
search-indexer-…  failed    2026-10-26T09:41Z
```

The ellipsis is the only truncation marker, so there's nothing extra to add. STATUS stays as a word even when you color it, so it doesn't rely on color.

---

## 2. Showing where config values come from

### Precedence (highest wins), documented in `--help`

1. Command-line flags
2. Environment variables (`MYTOOL_LIMIT`, …)
3. Project config (`./mytool.toml`)
4. User config (`$XDG_CONFIG_HOME/mytool/config.toml`, falling back to `~/.config/mytool/`)
5. System config (`/etc/mytool/`)
6. Built-in defaults

Accept `--config PATH` and `MYTOOL_CONFIG`; the flag beats the env var.

### The command

```
$ MYTOOL_LIMIT=100 mytool config list --show-origin
SOURCE   ORIGIN                                 KEY      VALUE
project  ./mytool.toml                          limit    50
env      MYTOOL_LIMIT                           limit    100        (wins)
user     /home/ann/.config/mytool/config.toml   format   "table"
default                                         color    "auto"
user     /home/ann/.config/mytool/config.toml   token    ****       (redacted)
```

Design notes:
- Show **overridden** layers too, not only the winner. Users run this command because the value isn't the one they expected, and they need to see what beat it.
- **Redact secrets** every time. Better still, keep tokens out of plain config entirely (use the OS keychain or `--token-stdin`), and never accept a secret as a flag value.
- Add `--json` with `{"key","value","source","origin","overridden_by"}` per entry, for support scripts and bug reports.
- An optional `mytool config get limit --show-origin` gives a one-line answer.
- Precedents: `git config --show-origin`, `npm config list -l`, `aws configure list`.

---

## Tests to pin down

- Golden tests of stdout, stderr, and the exit code for: under the limit (no note), exactly at the limit, over the limit with a total, over the limit without a total, `--paginate` failing midway, and `-q`. Run each with no TTY and under `NO_COLOR`.
- `--json` documents with and without `next_cursor`; NDJSON with nothing but objects on stdout.
- The table at 80 and 60 columns with CJK or emoji names.
- Precedence: set the same key at every layer and assert the winner and the `(wins)` marker. Assert that secrets never appear in plain or `--json` output.

If you tell me the language you're using, I can sketch the flag parsing, the layered config resolver, and the golden tests in its usual libraries.
