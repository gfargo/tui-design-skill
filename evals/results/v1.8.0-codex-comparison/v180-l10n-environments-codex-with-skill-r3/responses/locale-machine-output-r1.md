Treat the human table and `--json` as separate output contracts.

- **Human table:** honor the numeric locale. The same size may display as `1,234.5 MB` in US English and `1.234,5 MB` in German. Respect `LC_ALL` → `LC_NUMERIC` → `LANG`. Document that formatting and rounded values are for people.
- **JSON:** remain locale-independent. Emit exact sizes as numeric bytes, such as `{"size_bytes":1234500000}`, rather than `"1.234,5 MB"`. Keep field names, types, and unit meanings stable. JSON numbers never have grouping separators and use `.` for decimals.
- **Units:** define `MB` as 1,000,000 bytes and `MiB` as 1,048,576 bytes. Apply rounding only when displaying human sizes.
- **Streams:** JSON results go to stdout; diagnostics go to stderr. No headings, color escapes, progress indicators, or localized prose in JSON stdout.
- **Automation:** recommend `--json` explicitly. Redirecting a table to a pipe does not make its formatting a stable API.
- **Verification:** test identical JSON data under `C`, `en_US.UTF-8`, and `de_DE.UTF-8`, including locale overrides; separately test localized human formatting.

For the affected user, recommend migrating the script to `--json`. `LC_ALL=C your-cli …` can temporarily pin table formatting, but still leaves the script dependent on rounded values and table layout. If JSON itself changed with `LANG`, that is a bug to fix.