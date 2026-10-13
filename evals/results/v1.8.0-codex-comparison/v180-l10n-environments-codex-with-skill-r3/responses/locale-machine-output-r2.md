**Human output may follow locale; machine output must stay locale-independent.** Make that an explicit contract:

- **Human tables:** Honor numeric locale (`LC_ALL` → `LC_NUMERIC` → `LANG`). English might display `1,234.5 MB`; German `1.234,5 MB`. Document that tables contain rounded, localized presentation values and are unsuitable for parsing.
- **`--json`:** Emit raw values with stable field names and types, preferably exact byte counts: `{"size_bytes":1234500000}`. Never apply grouping, decimal commas, translated keys, or human-readable units to numeric fields. Document `MB = 1,000,000 bytes` and `MiB = 1,048,576 bytes`.
- **Streams:** JSON goes to stdout; diagnostics and progress go to stderr. JSON contains no headers, ANSI styling, or truncation. Keep the same schema when redirected or piped.
- **Compatibility:** Treat changes to JSON fields, types, units, or meaning as API changes. If JSON currently contains only formatted size strings, add a raw field and provide a migration period.
- **Verification:** Test identical JSON values and types under `C`, `en_US.UTF-8`, and `de_DE.UTF-8`, including conflicting locale overrides. Test localized tables separately.

For the affected user, recommend parsing `--json`’s raw size field. `LC_ALL=C your-cli …` can temporarily stabilize the table’s locale, but its rounding and layout still make it a fragile scripting interface.