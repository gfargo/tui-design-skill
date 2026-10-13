**Recommendation:** treat the two outputs as different contracts. The human table follows the user's locale and can change between releases. `--json` (and any `--plain` or `--csv`) never depends on locale, and scripts must be pointed at it.

### What probably broke

With `LANG=de_DE.UTF-8`, a locale-aware formatter prints `1,234.5 MB` as `1.234,5 MB`. The German locale swaps the two separators. The fix depends on which output the script reads:

- **If it parses the human table**, our bug is that we never told users the table isn't a stable interface. The fix on their side is to switch to `--json`.
- **If it parses `--json`**, the bug is ours and it's serious. Somewhere a number in the JSON goes through a formatter that follows the locale (`printf("%f")`, `toLocaleString`, a C library that reads `LC_NUMERIC`), so the output becomes `1234,5`. That's either invalid JSON or a different value.

Ask the user which output they parse. Then check the JSON path either way, because the second case breaks every script for every user with a comma-decimal locale.

### The rules

**1. Human table: format for the user's locale, and don't promise stability.**
- Use the platform's locale library (`Intl.NumberFormat`, Babel, `golang.org/x/text/message`, ICU4X). Don't hand-build strings. If we currently hardcode `,` and `.`, German users see English formatting, which is also wrong.
- Find the locale by checking `LC_ALL`, then `LC_NUMERIC`, then `LANG`, skipping empty values.
- Right-align the size column and pick one unit system. `MB` (10⁶) and `MiB` (2²⁰) are different numbers, so label whichever we use.
- State in the docs and `--help` that this output is for humans and may change.

**2. `--json`: same bytes in every locale.**
- Emit raw integer bytes as a JSON number: `"size_bytes": 1234500000`. No grouping, no units, no rounding. Consumers can format it themselves.
- Build the output with a real JSON serializer, never `printf` or string concatenation.
- If C code or a library that reads the locale is anywhere in the path, set `LC_NUMERIC=C` for machine output.
- If we add a human string, put it in a separate field (`"size_human": "1.2 GB"`) and keep it out of the parseable value.
- Treat this schema as a stable API. Make additive changes only, and give a deprecation warning one release ahead of any removal.

**3. `--plain` / `--csv` / TSV: same rule as JSON.** They're machine formats, so use C-locale numbers, no grouping, and raw bytes or a fixed documented unit.

**4. Don't switch number formats silently when output is piped.** Turning off color on a pipe is normal. Quietly changing the meaning of `1.234` is not. Scripts should ask for `--json` explicitly. Until they move over, `LC_ALL=C mycli …` makes the human table predictable, but tell users that's a workaround and not the supported interface.

### Tests to add
- **Golden test:** run `--json` (and `--plain`/`--csv`) under `C`, `en_US.UTF-8`, `de_DE.UTF-8`, `fr_FR.UTF-8`, and `hi_IN.UTF-8`. Assert the output is byte-identical every time and parses as valid JSON. The German and French cases catch comma decimals; Indian English catches `12,34,567` grouping.
- **Snapshot test:** check the human table under at least `en_US` and `de_DE`, so localized formatting doesn't regress.
- **Pin the locale in every other test.** CI environments differ: some run in the `C` locale, and GitHub's macOS runners set `LC_ALL=en_US.UTF-8`. Unpinned tests will pass or fail depending on the machine.

### Reply to the user
Something like: "The human table follows your locale and isn't meant for parsing. Use `--json` and read `size_bytes`, which is the same in every locale. If you're already using `--json` and it changed, that's a bug on our side and we're fixing it."

These rules come from the skill's localization guidance (`references/visual-patterns.md` → *Localization*) and its CLI stability rules (`references/cli-basics.md`: human output can change, machine output must stay stable).
