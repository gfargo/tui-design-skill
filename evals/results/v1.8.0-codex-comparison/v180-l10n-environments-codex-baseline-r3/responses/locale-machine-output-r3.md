Treat human display and machine output as separate contracts.

- **`--json` must be locale independent.** Emit file sizes as numeric byte counts, such as `"size_bytes": 1234500000`. JSON numbers use `.` for decimals and never grouping separators. Keep keys and units stable; don’t emit localized strings as the only representation.
- **Human tables may follow the locale.** English might show `1,234.5 MB`; German might show `1.234,5 MB`. Document that this output is for people and isn’t a stable parsing interface.
- **Provide deterministic display when needed.** Support a locale override, such as `--locale=C`, or document `LC_ALL=C` if your formatter honors it. This stabilizes formatting but doesn’t make rounded human sizes suitable for exact calculations.
- **Define units explicitly.** `MB` means 1,000,000 bytes; `MiB` means 1,048,576 bytes. Convert and round only for display.

Recommend that the affected script use `--json` and read `size_bytes`. Test machine output under both `C` and `de_DE.UTF-8` to ensure it stays identical.

If you previously promised that the human table was parseable or locale invariant, preserve that contract or introduce the change through a documented migration.