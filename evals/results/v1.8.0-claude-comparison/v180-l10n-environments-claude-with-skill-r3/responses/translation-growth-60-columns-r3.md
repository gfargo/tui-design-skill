**Short answer:** stop sizing anything from English. Before the strings arrive, make column widths come from the translated text measured in terminal cells, give every column a drop priority, make the footer fit the current width, and give translators a cell budget for each string. Then test with fake long strings at 60 columns now, so you aren't finding the breakage when real translations land.

## 1. Make the table adapt to whatever the strings turn out to be

Translations grow most on short strings. Allow 100–200% extra for anything under 10 characters, and headers, statuses and key hints are all that short. Japanese characters take two cells each, so 優先度 ("priority") is 6 cells wide, not 3. Some likely examples:

| | English | German | Finnish | Japanese |
|---|---|---|---|---|
| Header | Priority | Priorität (10) | Prioriteetti (12) | 優先度 (6) |
| Status | In progress | In Bearbeitung (14) | Käynnissä (9) | 進行中 (6) |

So:

- **Measure in cells.** Find column widths in `tea.WindowSizeMsg` as the larger of `lipgloss.Width(header)` and the widest value, using the current locale's strings. Search the code for `len(` on display text and for `%-Ns` padding. Go's `fmt` pads by runes, not cells, so Japanese rows will misalign.
- **Drop columns by priority, not at fixed widths.** If a cutoff like "hide Priority below 76" is tuned for English, it will be wrong for German. Remove the lowest-priority column until what's left fits, and German will fold earlier on its own:

```go
// want = max(lipgloss.Width(header), widest cell), measured per locale.
// Title has a min and absorbs the leftover width.
for len(cols) > 1 && totalWant(cols, gap) > m.width {
    cols = dropLowestPriority(cols) // Priority → Due → Status
}
```

- **Add detail-on-Enter** so a hidden column is one keypress away. If high priority matters, show a marker only on the high-priority rows (`! ` plus the word in the detail view), not a marker on every row.
- **Truncate, don't wrap.** Cut titles at the end with `…`, keep a cell for the ellipsis, and let labels truncate before data does.
- **Clutter check at 60 columns.** The default Bubbles table pads every cell by one on each side, which is 8 cells of padding across 4 columns, plus any border. Don't put the table in a box of its own; the terminal edge already frames it.

At 60 columns, German would look roughly like this:

```
Aufgabe                        Status          Fällig
Steuererklärung abschicken     In Bearbeitung  2026-10-20
! Zahnarzttermin vereinbar…    Offen           2026-10-14
↑/↓ bewegen · enter Details · n neu · / filtern · ? Hilfe
```

How it should behave at each size:
- **≥80 columns:** all four columns.
- **About 60 columns:** Priority moves to the detail view.
- **Narrower:** Title and Status only, using short status forms.
- **Below the real minimum:** a translated message such as `Terminal zu klein — mindestens 40×10 nötig`. It should name your actual minimum, not 80.

## 2. Make the footer fit the width

- Use `bubbles/help` driven by your `key.KeyMap` and set its width from the window size. When hints don't fit, it drops them from the end and shows `…`, so **order `ShortHelp()` by importance and put `? help` early** so it is never the one dropped. The `?` screen then holds everything.
- Show 3–5 hints for the current context, not the whole keymap.
- **Don't translate key names**, and keep the bindings the same in every locale. `d` stops being a mnemonic in German (`d löschen`); that's fine. Changing keys per language breaks docs and muscle memory.

## 3. What to give translators

- **A cell budget and context for each string**, for example: `footer.delete: imperative verb, ≤8 cells (CJK = 2 cells/char)`.
- **Short variants** for anything the layout may squeeze: `status.in_progress` plus `status.in_progress.short`, and short header forms.
- **No string concatenation, and proper plurals.** German and Finnish have one/other plural forms; Japanese has only other. Use `golang.org/x/text/message` or go-i18n rather than `fmt.Sprintf("%d " + tasks)`.
- **Dates:** keep fixed-width ISO-8601 in the table. Format dates and numbers for the user's locale only in prose and the detail view. Keep `--json` and `--plain` output independent of locale.

## 4. Ambiguous-width characters (this mainly affects Japanese users)

`…`, `·`, `•`, `↑↓←→` and almost all box-drawing characters, including rounded corners, are "ambiguous width." Many Japanese users set their terminal to draw these two cells wide. go-runewidth also switches to wide under a `ja` locale, while most other width libraries assume narrow, so the app and the terminal can disagree about widths.

- Test with the terminal's ambiguous-wide setting turned on.
- Prefer separators that are always narrow, like `|`, or plain words.
- Keep an ASCII border and marker set available behind one setting (`--ascii`).

## 5. Test it before translations exist

- **Make a pseudo-locale** where every string is about 50% longer and wrapped in markers (`[Ŧîţļé ŵîţĥ ĥéàð…]`), plus a second one in fullwidth CJK. `podebug` or a 20-line script can generate them.
- **Golden-test each locale** at 80×24, 60×24 and your minimum. Use `teatest/v2` with `tea.WithColorProfile(colorprofile.ASCII)` and pin `LANG`/`LC_ALL` in CI.
- **Unit-test resize** by sending `tea.WindowSizeMsg{Width: 60, Height: 24}` and checking that columns drop in the right order.

If the pseudo-locale works at 60 columns, the real German strings almost certainly will too. If it breaks, you found out before paying for translations.
