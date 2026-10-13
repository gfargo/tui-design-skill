Treat human display and machine output as separate contracts.

- **Default table:** Keep formatting stable across locales—e.g. `1,234.5 MB`—unless users explicitly request localized output. Changing `LANG` alone shouldn’t silently change your existing output.
- **Localized display:** Offer an explicit option such as `--locale=de-DE`, which could display `1.234,5 MB`. Document human tables as presentation output whose layout and rounding may change.
- **`--json`:** Always emit locale-independent JSON. Represent sizes as integer bytes, e.g. `{"size_bytes":1234500000}`, rather than a formatted string. JSON numbers never use grouping separators or decimal commas. Keep keys and enum values untranslated.
- **Units:** Define them precisely: MB = 1,000,000 bytes; MiB = 1,048,576 bytes. Round only for display; preserve the exact byte count in machine output.
- **Compatibility:** Treat the JSON schema as a supported interface. Document and manage breaking changes.

For this incident, restore the previous default table formatting and tell the user to migrate their script to `--json`. Setting `LC_ALL=C` can be a temporary workaround if the current formatter honors it, but parsing a rounded human table remains fragile.