I didn't find any Go files in the working directory, so this advice is general rather than based on your code. I'm assuming you use `bubbles/table`, `bubbles/help`, and lipgloss.

The main thing to fix first: your layout fits 80 columns of English, and you need it to fit 60 columns of German. German UI text usually runs about 30–40% longer than English, and Finnish has long compound words. Japanese uses fewer characters, but each one takes two terminal cells and there are no spaces to wrap on. Make these changes before strings arrive.

## 1. Measure in terminal cells, not bytes or characters

- Don't use `len(s)` or `utf8.RuneCountInString(s)` for layout. Use `lipgloss.Width()` or `runewidth.StringWidth()`. For example, `進行中` is 3 characters but 6 cells.
- Truncate with `ansi.Truncate(s, w, "…")` (from `charmbracelet/x/ansi`) or `runewidth.Truncate`. Never slice strings, or you can cut a character or styling code in half.
- Avoid "ambiguous-width" glyphs like `…`, `→`, `●`, `★`, and some box-drawing characters. In a Japanese locale, terminals and tmux may draw them two cells wide while your code counts one, which misaligns every row. Use plain ASCII (`...`, `>`) in places where alignment matters, or set `runewidth.DefaultCondition.EastAsianWidth` to match the user's locale and test it.
- Don't use emoji or Nerd Font icons as column content. Their widths vary between terminals.

## 2. Compute column widths from the window size

Throw out hardcoded widths. On every `tea.WindowSizeMsg`:

```go
func layoutColumns(total int, headers []string) []table.Column {
    // Fixed columns: sized to the widest translated header or value, with a cap.
    status := clamp(maxWidth(headers[1], statusLabels...), 6, 14)
    due    := clamp(maxWidth(headers[2], sampleDates...), 5, 10)
    prio   := clamp(lipgloss.Width(headers[3]), 3, 8)

    gaps := 3 * cellPadding           // count separators and borders too
    title := total - status - due - prio - gaps

    cols := []table.Column{{Title: headers[0], Width: title}, ...}
    if title < 20 {                    // below the breakpoint, drop the least important column
        cols = dropPriority(cols)      // and give its width to the title
    }
    return cols
}
```

- Make one column (probably the task title) flexible. It gets whatever space is left.
- Choose which column disappears first when space runs out. At 60 cells with borders and gaps, four columns leave the title very little room once German headers arrive.
- Status values are the worst offenders: "In Progress" becomes "In Bearbeitung" in German and "Käynnissä" in Finnish. Either ask translators for short forms with a fixed cell budget, or show a 1–2 cell symbol in the table and the full word in the detail view.
- Ask for an abbreviated version of each header, e.g. `header.priority` and `header.priority.short`, and use the short one when space is tight.

## 3. Footer of key hints

- Use `bubbles/help` and set `help.Width = msg.Width`. It drops hints that don't fit and shows an ellipsis.
- Order `ShortHelp()` by importance, because hints are dropped from the end. Always show `? help` so the rest can still be found.
- Translate the action descriptions, not the key names. Keep `enter`, `ctrl+c`, and `esc` as they are.
- Don't pick keys based on English words, like `d` for "delete" because the word starts with d. That connection disappears in translation, so don't make translators work around it.

## 4. Give translators width budgets

- For every string, give a maximum width in cells plus a screenshot or context note. Tell them that each Japanese character counts as 2 cells.
- Add a CI check that runs `runewidth.StringWidth` on every translated string against its budget. That way, an overflow fails the build instead of showing up in a bug report.
- Use proper message formatting (`go-i18n`, ICU-style placeholders and plural forms). Never build text like `fmt.Sprint(n) + " " + T("tasks")`. Finnish noun endings and Japanese word order won't work with that.
- Format dates through locale-aware functions, and budget for the longest result (German date formats and month names are long).

## 5. Test before the real strings arrive

- **Pseudo-localization:** add a fake locale that makes every string about 40% longer with accented letters (`[Ťåšķš ŧő đő ~~~~]`), plus a full-width variant (`Ｔａｓｋｓ`). Run it at 60 columns now. Most of the bugs above will show up immediately.
- **Golden tests:** use `teatest` to snapshot each locale (en, pseudo, de, fi, ja) at 60, 80, and 120 columns. Include a very narrow width like 40 to make sure nothing panics on a negative width.
- **Manual check:** run it inside an actual 60-column tmux pane with `LANG=ja_JP.UTF-8`. That's how you'll find the ambiguous-width problems.

**If you only do three things:** measure everything with `lipgloss.Width`, recompute column widths on every resize with one flexible column and a rule for dropping columns, and add the pseudo-locale with 60-column golden tests. Once those are in, translated strings are much less likely to break the layout.
