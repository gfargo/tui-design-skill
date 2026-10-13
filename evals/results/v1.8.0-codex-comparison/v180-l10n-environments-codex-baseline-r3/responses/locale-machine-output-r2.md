Treat human display and machine output as separate contracts.

- **`--json` must be locale-independent.** Emit sizes as integer bytes, for example `{"size_bytes":1234500000}`. JSON numbers never use grouping separators or decimal commas. Keep keys and unit definitions stable across locales.
- **Choose and document a human-formatting policy.** Either use a fixed format everywhere or honor the user’s locale consistently. Under German formatting, `1,234.5 MB` becomes `1.234,5 MB`. If your existing table has effectively been a stable interface, changing its default formatting deserves compatibility consideration.
- **Tell scripts to use `--json`.** Human tables can change spacing, precision, units, translations, and separators. Don’t promise that they are parseable unless you explicitly support that contract.
- **Keep machine stdout clean.** In JSON mode, send diagnostics to stderr and omit progress indicators, colors, and explanatory text from stdout.

For this CLI, I’d preserve the existing human format by default, offer localized formatting explicitly if useful, and make JSON with integer byte counts the supported scripting interface.

Also investigate the actual locale source: `LC_ALL` overrides `LC_NUMERIC`, which overrides `LANG` for numeric formatting. Setting `LANG` alone may not explain the behavior if those variables are present.