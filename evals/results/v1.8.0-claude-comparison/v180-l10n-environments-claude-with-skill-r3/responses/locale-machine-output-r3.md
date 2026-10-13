**Rule: the human table follows the user's locale, and anything a script reads never does.** Under `de_DE`, `1,234.5 MB` correctly becomes `1.234,5 MB` in the table. `--json` (and `--plain`, if you have it) must print exactly the same bytes whatever `LANG`, `LC_ALL` or `LC_NUMERIC` is set to.

## The rules

1. **Human table: format with the locale.** Separators, grouping and even digits vary by locale. The same number is `1.234.567,891` in German, `1 234 567,891` in French and `12,34,567.891` in Indian English. Use your platform's locale library (`Intl.NumberFormat`, Babel, `golang.org/x/text/message`, ICU4X) rather than building the string by hand. Keep numbers right-aligned and dates in fixed-width ISO-8601 (`2026-10-13 14:30`), which reads the same in every locale.

2. **Machine output: never depend on the locale.** In `--json`:
   - Emit raw values, not display strings: `"size_bytes": 1234500000`, not `"size": "1,234.5 MB"`. Scripts shouldn't have to parse your units or your rounding.
   - Write numbers with your JSON encoder, never with a locale-aware `printf`/`sprintf`. In C, or any runtime that calls `setlocale(LC_ALL, "")`, `printf("%.1f")` prints `1234,5` under `de_DE`. Inside JSON that is a syntax error or a silently wrong value. If you must shell out or use C formatting for machine output, pin `LC_NUMERIC=C` for that path.
   - Apply the same rules to `--plain`/TSV output if you offer it.

3. **Document the contract.** Say plainly that the human table is unstable and localized, and that `--json` is the stable interface. Changes to the JSON field names, types or units should be treated as breaking changes; changes to the table are not.

4. **Test both sides with a pinned locale.** CI environments differ (GitHub's macOS runners set `LC_ALL=en_US.UTF-8`, others run in `C`), so set the locale explicitly in tests:
   - Golden-test `--json` under `C`, `en_US.UTF-8` and `de_DE.UTF-8`, and assert the output is byte-identical.
   - Snapshot the human table under `de_DE.UTF-8` and check that `1.234,5 MB` stays right-aligned and fits the column.

## Diagnosing this report

Ask the user which output their script reads:

- **If it parses the human table,** the script is relying on output you never promised to keep stable. The fix on their side is `--json` plus `jq`, e.g. `jq '.size_bytes'`. On your side, document that, and consider adding a `--plain` mode for people who want plain columns.
- **If it parses `--json`,** you have a real bug: some number is going through locale-aware formatting. Check whether the JSON is still valid under `LANG=de_DE.UTF-8`. A field like `1234,5` or a pre-formatted size string will show up immediately. Fix it by emitting raw numbers with the encoder and add the locale golden test above.

A separate point worth settling while you're here: decide whether "MB" means 10⁶ or 2²⁰ bytes, and use `MiB` in the table if you mean the latter. Emitting `size_bytes` in JSON makes this a display-only question for scripts.
