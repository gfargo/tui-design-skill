Your list command is a one-shot CLI, so I based this on the skill's CLI reference (`cli-basics.md`) plus its table-truncation rules (`visual-patterns.md`).

## Recommendation

1. **Bounded by default.** Add `--limit N` with a finite documented default (gh uses 30). Add `--paginate` to fetch everything. Don't do both: pick one default per tool.
2. **Say when output was cut off.** Write a one-line note to stderr that names the flag that gets the rest. Exit 0, because returning fewer rows on request isn't an error.
3. **Shorten cells to fit the screen only on a TTY.** When output is piped, write full values. Add `--no-truncate` for terminals.
4. **Add `config list --show-origin`.** It prints each effective value, where it came from, and which source won, with secrets redacted.

There are two kinds of truncation here, and they shouldn't be confused:

| | Row limit (`--limit`) | Cell truncation (width) |
|---|---|---|
| What it is | How many records you fetch | How a long value fits a column |
| Applies when piped? | Yes (it controls fetching) | No: piped output gets full values |
| Signal | Note on stderr | `…` in the cell |
| Override | `--limit N`, `--paginate` | `--no-truncate`, `--json` |

## Row limits and pagination

```
$ mytool list > items.txt
note: showing 30 of 1040 items; pass --limit N or --paginate for more
$ echo $?
0
```

- **stdout carries only results; the note goes to stderr.** That keeps `items.txt` and `| wc -l` accurate. Hide the note under `-q`.
- **If the API returns no total**, don't make one up. Write `note: showing first 30 items; more available (--paginate)`. Only print the note when the API says another page exists.
- **Make `--paginate` the only way to ask for everything.** Reject `--limit 0` or negative values with a usage error (exit 2) rather than guessing whether 0 means "none" or "unlimited".
- **Show results as each page arrives.** Print rows as pages come in, and flush on newlines. After about 150 ms, show progress on stderr, but only if stderr is a TTY.
- **Stop fetching when the reader leaves.** If `mytool list --paginate | head` closes the pipe, stop requesting pages and exit quietly (0 or 141, no stack trace).
- **Ctrl-C:** cancel the in-flight request and re-raise SIGINT. Don't `exit(130)`.

**Under `--json`:**

- Without `--paginate`, the result is bounded, so emit one document with the cursor inside it:
  ```json
  {"items":[…],"next_cursor":"eyJwIjoyfQ"}
  ```
  Add `--cursor TOKEN` so scripts can continue from where they stopped (the AWS `NextToken` model).
- With `--paginate`, the result is unbounded, so emit NDJSON: one object per line, nothing else on stdout. The "more" information goes only in the stderr note.
- Never send `--json` output through the pager.

## Cell truncation

Wide terminal (120 columns):
```
ID        NAME                              OWNER     UPDATED           STATUS
a1b2c3d4  billing-reconciliation-nightly    ann       2026-10-27 14:30  failed
e5f6a7b8  export/customers/2026/q3/full.csv raj       2026-10-26 09:12  ok
```

60-column tmux split:
```
ID        NAME                    UPDATED           STATUS
a1b2c3d4  billing-reconciliatio…  2026-10-27 14:30  failed
e5f6a7b8  …/2026/q3/full.csv      2026-10-26 09:12  ok
```

- **Which columns give way first:** low-priority columns drop entirely (OWNER above), then the flexible text column shrinks. One addition beyond the reference: keep the ID column at full width. It's the value people copy into the next command, so a truncated ID is useless.
- **Where to cut:** cut names and prose at the end. Cut paths at the start or middle so the filename survives. Leave one cell for `…`, or three for `...` when the terminal may not support Unicode.
- **Measure terminal cells, not string length.** CJK text and emoji will break column alignment otherwise.
- **No borders.** One record per line, with headers you can turn off via `--no-headers`. Right-align numbers, and use fixed-width ISO dates.
- **Status words are already text,** so color can reinforce them but they don't depend on it. Honor `NO_COLOR`.

## Showing where config values come from

Use a fixed precedence order (highest wins): flag → env (`MYTOOL_*`) → project config → user config (`$XDG_CONFIG_HOME/mytool/`) → system config → built-in default. Accept `--config PATH` and `MYTOOL_CONFIG`, with the flag beating the env var.

```
$ mytool config list --show-origin
SOURCE   LOCATION                                KEY     VALUE
user     /home/ann/.config/mytool/config.toml    limit   100
env      MYTOOL_LIMIT                            limit   50       (wins)
project  ./mytool.toml                           format  "json"
default                                          color   "auto"
keychain                                         token   ********
```

- **List shadowed values too, and mark the winner.** "Why is my config ignored?" is almost always one source overriding another.
- **Redact secrets.** Show the source, never the value. Tokens shouldn't come from flags anyway; use the keychain, a `--token-file`, or stdin.
- **Support `--json`** on this command too, so scripts and bug reports can capture it.
- **Link the two features (optional).** When `limit` came from config or env rather than the built-in default, add it to the note:
  `note: showing 50 of 1040 items (limit from MYTOOL_LIMIT); pass --limit N or --paginate for more`
  That answers "why do I only get 50?" without a trip to the docs.

## What to test

Use golden tests for stdout, stderr, and the exit code, with no TTY and with `NO_COLOR` set:
- the limit-hit note on stderr with exit 0;
- the API returning no total;
- `--json` including `next_cursor`, and `--paginate --json` producing pure NDJSON;
- `| head` stopping the page fetches;
- tables rendered at 120 and 60 columns, with CJK names;
- `config list --show-origin` with the same key set in several sources at once.

If you tell me your language or CLI framework (Cobra, clap, Click, oclif…), I can show how to wire the flags and track where each config value came from.
