The main change is to stop sizing anything from the English strings. Size columns and the footer from the cell width of the translated text at runtime. Make the layout change by width band instead of overflowing. Then test it with a pseudo-locale now, before any real translations arrive. Treat 60 columns as a supported layout, not an edge case.

Here's the work in priority order, using the Bubble Tea / Lipgloss / Bubbles stack.

## 1. Fix the string pipeline first (translators depend on this)

- **Keep key and action as separate strings.** `key.WithHelp("a", T("add"))` lets translators change only the action word, while the key stays the same in every locale. Never ship `"a add"` as a single catalog entry. Also don't build sentences by joining pieces together. Use `golang.org/x/text/message` (or go-i18n) for plurals: Finnish has plural forms, Japanese has none, and "3 tasks" built by joining strings is wrong in both.
- **Give translators budgets in cells, not characters.** A Japanese character takes two cells: 絞り込み ("filter") is 4 characters but 8 cells. In the brief, give each string a cell limit and a note on where it appears, for example "column header, ≤10 cells" or "footer action, ≤8 cells".
- **Ask for a short form of every column header and footer action** (`col.priority` plus `col.priority.short`). German compounds and Finnish words grow the most in exactly these short strings: "done" becomes "erledigt" or "valmis", "priority" becomes "Prioriteetti". Budget for short strings to double or triple in length.
- **Don't translate the keys.** `q` stays `q` even when the action is "beenden". Changing mnemonics per locale breaks muscle memory and the docs.

## 2. Measure everything with `lipgloss.Width()`

- Anywhere you size or pad with `len()`, a hard-coded width, or a width taken from the English header, it will break for Japanese. Find those places now.
- Bubbles `table.Column.Width` is fixed. On every `tea.WindowSizeMsg`, and when the locale loads, recompute the columns and call `SetColumns`. Each fixed column gets `max(lipgloss.Width(translated header), widest value)`, with a cap. The title column takes whatever width is left.
- Truncate cells, never wrap them. Leave room for `…`, and make sure truncation never cuts a wide character in half. The full value goes in a detail view (Enter).

## 3. Width bands for the 4-column table

I'm assuming your columns are status, title, due and priority. Swap in your real ones.

| Width | Behavior |
|---|---|
| ≥80 | All 4 columns with full translated headers. |
| 60–79 | Title fills the space. Status shrinks to a 1-cell symbol (`✓` `✗`, with the word in the detail view). Due shrinks to `MM-DD`. Headers switch to their short forms. |
| ~45–59 | Drop the lowest-priority column. Enter shows everything. |
| below the minimum | Show a translated "terminal too small — need 40×10" message. **That message must itself fit the minimum width in all four locales.** |

At 60 columns with no outer border, German fits like this:

```
  Aufgabe                                     Fällig  Prio
✓ Steuererklärung abschicken                  10-13   1
  Angebot für Kunde überarbeiten und send…    10-15   2
```

Show the selected row in reverse video instead of an extra marker column.

## 4. Footer: put hints in priority order and keep help visible

- Order `ShortHelp()` by importance. Render `? help` separately, aligned right, and set `help.Width = m.width - lipgloss.Width(helpHint)`. The help bubble then drops the hints that don't fit and adds `…`. "Hilfe", "ohje" and "ヘルプ" stay on screen in every locale, so dropped hints are one key away.
- Separate hints with two spaces instead of ` · `. With six hints that saves 6 cells. It also removes an ambiguous-width character (see the next section).

## 5. Japanese-specific risks

- **Ambiguous-width characters.** Box drawing (including rounded corners), `…`, `·`, `•` and the arrows `↑↓←→` can render one or two cells wide depending on the terminal setting. Many Japanese users turn on the "ambiguous = wide" setting. go-runewidth also switches to wide under a `ja` locale, while most other width libraries default to narrow. If two parts of your stack disagree, borders and columns misalign. Test with `LANG=ja_JP.UTF-8` and the terminal's ambiguous-wide setting on. Prefer `▸ ✓ ✗` for markers, and keep an ASCII border set one switch away.
- **Wrapping in detail views.** Japanese has no spaces, so any word wrapping that splits on spaces won't work. Test it on real Japanese prose.
- **Dates.** Keep fixed-width ISO dates in the table. Format other human-facing numbers and dates per locale. Keep `--json` and plain output locale-independent.

## 6. Test before the translations arrive

- **Pseudo-locales.** Make one that lengthens every string by about 50% (more for short ones) and wraps it in markers, e.g. `[Ăďď ţåšķ~~]`. Make a second that converts strings to full-width characters to simulate double-width text.
- **Golden tests.** Use teatest v2 with `tea.WithColorProfile(colorprofile.ASCII)`. Cover {en, pseudo-long, pseudo-wide, de, fi, ja} at 80×24, 60×24 and your minimum. Add a test that sends `tea.WindowSizeMsg{Width: 60, Height: 24}` mid-run and checks that the layout reflows. Pin the locale in CI.
- For a manual check, `tmux split-window -h` gives you a narrow terminal for free.

## Clutter audit: cells to recover first

I can't count your actual layout without seeing it. These are the usual places to win back space at 60 columns:

- **Outer border around the table:** costs 2 columns and 2 rows. Remove it; the terminal edge already frames the app.
- **Header underline row:** replace it with a bold or dim header.
- **Repeated status signals:** if status is shown as a word plus a color plus an icon, keep one of the two visual signals plus the word in the detail view.
- **`·` footer separators:** 3 cells each.

If you share the current `View()` or a screenshot, I can give you exact cell budgets for each column and footer string to put in the translator brief.
