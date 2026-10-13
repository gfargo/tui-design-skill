**Rule: the human table follows the user's locale, and machine output never does.** `--json` (and any `--plain` or TSV mode) should print the same bytes whether `LANG` is `C`, `en_US`, or `de_DE`. The human table isn't a parsing contract. Document that, and send script authors to `--json`.

### 1. First, work out which output broke

- **If the script parsed the human table**, the tool behaved correctly. Under `de_DE`, `1,234.5 MB` correctly becomes `1.234,5 MB`. Tell the user to switch to `--json`, and make your docs say clearly that table formatting can change with locale, terminal width and version.
- **If `--json` changed**, it's a bug in your tool. Fix it and say so in the changelog. Machine output is the stable contract scripts depend on.

### 2. Human table rules

- **Format with a locale library, not hand-built strings.** Use `Intl.NumberFormat`, Babel, `golang.org/x/text/message` or ICU4X. Separators, grouping and even digits vary by locale. For example, 1234567.891 is `1 234 567,891` in French and `12,34,567.891` in Indian English.
- **Resolve the locale in this order:** `LC_ALL`, then `LC_NUMERIC`, then `LANG`, skipping empty values. Fall back to `C` (or `POSIX`) if none are set.
- **Scale units so grouping separators rarely appear.** `1,234.5 MB` should really be `1.2 GB`. Pick a precision, such as 3 significant figures, and choose either SI (`MB`, powers of 1000) or IEC (`MiB`, powers of 1024). Document which one you use.
- **Right-align numbers and measure cell width, not byte length.** French groups digits with U+202F, a narrow no-break space. It takes one terminal cell but three bytes in UTF-8, so padding by byte length misaligns columns.

### 3. Machine output rules (`--json`, `--plain`, `--csv`)

- **Emit raw integers:** `"size_bytes": 1234500000`. Don't output `"1,234.5 MB"` or a rounded float. Integers avoid locale problems, rounding and unit ambiguity all at once.
- If you want a display string too, add it as a separate field (`"size_human": "1.2 GB"`) and document it as display-only. It isn't part of the stable contract.
- **Make sure the formatting path itself is locale-independent.** This is where these bugs actually come from:
  - **C/C++:** once you call `setlocale(LC_ALL, "")`, `printf("%f")` prints commas under `de_DE`, and `strtod` expects them. Format machine output with `LC_NUMERIC` pinned to `C`, or use a locale-independent formatter.
  - **Python:** `str(float)` and `json.dumps` don't depend on locale. `locale.format_string` and the `n` format spec do.
  - **JS:** `Number.prototype.toString` and `JSON.stringify` don't depend on locale. `toLocaleString` and `Intl` do.
  - **Go:** `fmt` never uses the locale, so the risk is only code that calls `x/text/message` on the machine path.
- Prefer NDJSON for streaming, and treat any field change as a breaking change with a deprecation period.

### 4. Input rules

Size arguments like `--min-size 1.5G` should always accept `.` as the decimal separator, whatever the locale. Otherwise a script works in one shell and fails in another. If you want, accept a locale-formatted value only in interactive prompts.

### 5. Tests that would have caught this

- Run the same command under `LANG=C`, `LC_ALL=de_DE.UTF-8`, `fr_FR.UTF-8` and `hi_IN.UTF-8`. Assert that `--json` output is **byte-identical** across all of them.
- Snapshot-test the human table per locale, with the locale pinned. Don't let CI's default leak in: some runners set `LC_ALL=en_US.UTF-8`, others run in `C`.
- Add a French-locale snapshot at 80 columns to catch the U+202F alignment problem.

**Suggested reply to the user:** "Table output is localized for reading and isn't meant to be parsed. Use `--json`, which reports `size_bytes` as an integer and doesn't change with locale." If their script was already using `--json`, apologize, fix it, and add the cross-locale byte-identical test.
