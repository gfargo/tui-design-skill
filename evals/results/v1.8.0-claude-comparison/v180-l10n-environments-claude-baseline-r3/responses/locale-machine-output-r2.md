I'd base the rules on one split: **human output follows the user's locale, and machine output never does.** Your user's script was probably parsing the human table, which is a contract you never meant to offer. It's still worth confirming that `--json` didn't change too, because if it did, that's a real bug.

## Rules

**1. The human table is for people, so localize it fully.**
- Follow the standard precedence: `LC_ALL` > `LC_NUMERIC` > `LANG`. A German user should see `1.234,5 MB`.
- `LC_ALL=C` (or `POSIX`) gives plain, unlocalized output. That's the conventional way to turn localization off, so make sure it works.
- Document that the table's layout and number format can change between releases and locales, and that scripts shouldn't parse it.

**2. `--json` is the contract, and locale never affects it.**
- Sizes are integer bytes with the unit in the key, e.g. `"size_bytes": 1294467072`. Not `"1,234.5 MB"`, and not a float in MB.
- Never put locale-formatted numbers inside strings, e.g. `"size": "1.234,5"`.
- Use your language's locale-invariant serializer. Watch for code paths that format numbers with locale-aware helpers before serializing (`printf("%'.1f")`, `toLocaleString`, `Intl.NumberFormat`, Python `locale.format_string`).
- Keep timestamps in ISO 8601 / RFC 3339 UTC and enums as stable identifiers, not translated labels.
- Add a regression test that runs `--json` under `LANG=de_DE.UTF-8`, `fr_FR.UTF-8` and `C` and checks that the output is byte-identical.

**3. Offer a plain-text machine format if people script with `grep`/`awk`.**
- A `--porcelain` or `--format=tsv` mode: tab-separated, no header (or a fixed one), raw bytes, locale-invariant, stable across versions.
- Optionally add `--bytes` to make the human table show exact byte counts.

**4. Don't switch formats based on whether output is a TTY.**
- Colour and truncation can depend on the TTY. Number formatting shouldn't, or the same command will behave differently in a terminal and in a pipe, which confuses everyone.

**5. Choose your size units and stick to them.**
- `MB` (10⁶) and `MiB` (2²⁰) are different. Choose one for the human table and label it correctly.
- Auto-scale for readability: `1.2 GB` reads better than `1,234.5 MB`.
- JSON avoids this problem entirely by using bytes.

**6. Version the machine contract.**
- Adding JSON fields is fine. Renaming or removing fields, or changing their types, is a breaking change and should go in the changelog.

## For this user
- **If they parse the table:** point them to `--json` (or `--porcelain`), with `LC_ALL=C` as the immediate workaround.
- **If they already use `--json` and it changed under `de_DE`:** that's a bug on our side. Fix it and add the locale test from rule 2.

I haven't looked at your code. If you point me to where the size formatting and JSON output are built, I can check whether locale is leaking into the JSON path.
