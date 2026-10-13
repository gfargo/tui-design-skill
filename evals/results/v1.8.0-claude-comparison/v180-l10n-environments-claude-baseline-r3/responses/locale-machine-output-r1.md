Split the output into two contracts: the human table is for reading and may follow the user's locale, while `--json` is the stable interface for scripts and must never change with locale. Your user's script was parsing the human table, which isn't a supported interface. Point them to `--json`. Also check that `--json` itself doesn't change under `de_DE`, because that would be a real bug on your side.

## Rules

**1. `--json` (and any CSV or porcelain mode) is the same in every locale**
- Sizes are raw integer bytes: `"size_bytes": 1294467072`, not `"1,234.5 MB"`. Leave unit conversion to the consumer.
- No thousands separators. `.` is always the decimal point. Times use ISO 8601 / RFC 3339 in UTC.
- Key names and enum values are fixed English identifiers.
- Watch for this trap: in C, or anything that calls `setlocale(LC_ALL, "")`, `printf("%.1f")` prints `1234,5` under `de_DE`. In a JSON number that's **invalid JSON**. Use a JSON library or locale-independent formatting (`uselocale`, `snprintf_l`, or a `"C"` locale object). Python's `json`, Go's `encoding/json` and Rust's `serde_json` are already safe.

**2. The human table may be localized, and the docs should say it's not for parsing**
- If you localize, respect the POSIX order of precedence: `LC_ALL` > `LC_NUMERIC` > `LANG`. `de_DE` gives `1.234,5 MB`. `LC_ALL=C` or `POSIX` gives `1,234.5 MB` or a plain `1234.5 MB`.
- Pick one unit system and keep it the same everywhere. Use MB (10⁶) or MiB (2²⁰) and label it correctly. The unit system is not a locale setting.
- Add a line to the docs and the `--help` text: *"Table output is for humans and may change between versions and locales. Use `--json` for scripting."*

**3. Give people a simple option between the two**
- Add a flag like `--bytes` / `-b` (compare `ls -l` with `ls -lh`) that prints raw integers in the table. Quick `awk` use then works without bringing in `jq`.
- Don't change number formatting automatically when stdout isn't a TTY. That causes "it works in my terminal but not in my script" confusion. Keep the switch explicit. Turning off color and paging when stdout isn't a TTY is still fine.

**4. Parse input without locale too**
- `--min-size 1.5G` should mean the same thing in every locale. Don't use locale-aware `strtod` or `atof` on arguments.
- Compare flags and enums without locale. Under `tr_TR`, `"ID".lower()` can give `ıd` (dotless ı) and break matching.

**5. Keep stdout clean**
- Warnings, progress and errors go to stderr, so `--json` stdout is always valid JSON on its own.

**6. Test it**
- Run the CLI tests under `LC_ALL=C`, `de_DE.UTF-8` and `tr_TR.UTF-8`. Check that the `--json` output is byte-identical across all three and passes a JSON validator.

## What to tell the user right now

> The table output is localized and isn't meant for parsing. Please switch to `--json` (sizes are in `size_bytes` as integers), e.g. `ourcli list --json | jq '.[].size_bytes'`. As a stopgap, `LC_ALL=C ourcli …` restores the old formatting.

If the human table used to ignore locale and only started localizing recently, scripts relying on it broke because of your change. In that case, mention it in the changelog as a behavior change even though the table was never a supported interface.
