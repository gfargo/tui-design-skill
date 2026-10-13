**Locale may affect human presentation; it must never affect the machine output contract.**

Adopt these rules:

- **Human table:** honor the numeric locale: `1,234.5 MB` might become `1.234,5 MB` in Germany. Follow `LC_ALL` → `LC_NUMERIC` → `LANG`. Document that rounded sizes, separators, and table layout are display formatting.
- **`--json`:** use a real JSON serializer and locale-independent values. Return exact bytes, for example `{"size_bytes":1234500000}`, rather than `"1.234,5 MB"`. JSON numbers have no grouping separators and always use `.` for decimals. Keep field names, types, and unit meanings stable.
- **Units:** define `MB = 1,000,000 bytes` and `MiB = 1,048,576 bytes`. Locale must not change that meaning.
- **Streams:** JSON alone goes to stdout; diagnostics go to stderr. No colors, progress, headers, or truncation in JSON, even on a TTY.
- **Automation:** explicitly recommend `--json`. Redirecting a human table into a pipe does not make its formatting a stable API.
- **Verification:** test identical JSON values and types under `C`, `en_US.UTF-8`, and `de_DE.UTF-8`, including locale overrides.

For this user, recommend extracting `.size_bytes` from `--json`. `LC_ALL=C` can temporarily stabilize the existing table parser, but rounding and layout still make it fragile.

If the broken script already uses `--json`, treat the locale dependence as a bug. If table parsing was previously promised as supported, provide a compatibility path and deprecation notice before changing that promise.