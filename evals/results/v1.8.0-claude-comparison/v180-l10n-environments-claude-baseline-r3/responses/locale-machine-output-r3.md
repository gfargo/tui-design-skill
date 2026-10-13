Treat this as two output contracts with different rules.

## Rules

**1. `--json` (and any other machine format) never depends on locale.**
- Sizes are integers in bytes: `"size_bytes": 1294467072`. Don't send preformatted strings like `"1,234.5 MB"`, and don't send pre-rounded floats.
- If you also want a display string, put it in a separate, clearly named field (`"size_human": "1.2 GB"`), and document that its format can change.
- Put the unit in the key name (`size_bytes`, `duration_ms`) so nobody has to guess.
- Format dates as ISO 8601 / RFC 3339 in UTC. Write booleans and enums as fixed ASCII tokens, never translated text.
- Make sure no locale-aware code runs on this path, including `printf("%'d")`, `toLocaleString`, `Intl.NumberFormat`, and `locale.format_string`. JSON requires `.` as the decimal separator anyway, so a locale leak here can produce invalid JSON, not just odd-looking numbers.
- Treat the schema as a stable API. Version it and don't change it casually.

**2. The human table can be localized and makes no stability promises.**
- Showing `1.234,5 MB` under `de_DE` is correct. That's what German users expect to read.
- Say in the docs and in `--help` that the table is for people and may change. Scripts should use `--json`.
- Follow POSIX precedence for number formatting: `LC_ALL`, then `LC_NUMERIC`, then `LANG`. That way users can run `LC_NUMERIC=C` to get plain numbers without changing their message language.
- Choose a unit convention and stick to it. Either use 1024-based sizes and label them MiB/GiB, or use 1000-based sizes and label them MB/GB. Mixing them causes a separate set of parsing bugs.

**3. Optional: offer a plain, stable text mode** such as `--porcelain` or `--format=tsv`. It would output raw bytes, tab-separated, with no header (or a fixed one), always locale-independent. This helps people writing `awk`/`cut` pipelines who don't want to use `jq`.

**4. Don't silently change number formatting based on whether output is a TTY.** Doing that makes bugs that only show up in pipes, which are hard to track down. Use explicit flags instead.

## For this bug report

Find out which output the user's script was parsing.
- **If it parsed the human table:** this is expected behavior. Point them to `--json`, or to `LC_ALL=C` as a quick workaround. Consider adding a note to the docs.
- **If it parsed `--json`:** this is a real bug on our side, and probably a high-priority one. Find the formatter that's reading the locale and remove it from the JSON path.

## Prevent regressions
Run the CLI test suite under several locales: `C`, `de_DE.UTF-8` (comma decimal), `fr_FR.UTF-8` (narrow no-break space as the thousands separator), and `tr_TR.UTF-8` (dotted/dotless i, which breaks case-insensitive key matching). Assert that `--json` output is byte-for-byte identical in all of them.
