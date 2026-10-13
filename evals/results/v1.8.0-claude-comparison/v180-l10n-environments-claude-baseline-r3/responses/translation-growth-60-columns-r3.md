The repo is empty, so this is based on how Bubble Tea and Lip Gloss layouts usually fail, not on your code. Roughly in priority order:

## 1. Measure terminal cells, not bytes or runes
This is the change most likely to break the Japanese build.

- `len(s)` counts bytes and `utf8.RuneCountInString(s)` counts characters. Neither is the screen width. Japanese kana and kanji take 2 terminal columns each.
- Use `lipgloss.Width(s)` or `ansi.StringWidth(s)` from `charmbracelet/x/ansi` everywhere you pad, align or truncate. Search the code for `len(`, `%-20s`, `fmt.Sprintf("%*s"` and `strings.Repeat(" ", ...)`. Each of those is a bug once wide characters appear.
- Truncate with `ansi.Truncate(s, w, "…")`. Never slice strings. Slicing can split a multi-byte character, or leave a column half-filled when a wide character won't fit.
- Avoid symbols whose width depends on the terminal (East Asian "ambiguous width"). Examples are `…`, `★`, `○`, `●`, `→` and `※`. In CJK locales some terminals draw them 2 columns wide, which pushes table borders out of line. Use ASCII, or test these glyphs in iTerm2, Terminal.app and Windows Terminal with a Japanese locale. Use `...` as the ellipsis if you see problems.

## 2. Make 60 columns the design target, not 80
- Expect German to run 30–40% longer than English, with long compound words. Finnish words are long too (e.g. "Määräpäivä", "Keskeneräinen"), and its case endings mean you can't reuse one word in different positions. Japanese uses fewer characters but takes about the same width, since each character is 2 columns.
- Wrapping that relies on spaces won't work. Japanese has no spaces, and German and Finnish compounds have no break points. `lipgloss.NewStyle().Width(w)` wraps on spaces and falls back to hard breaks. That's acceptable for body text but not for table cells. In cells, truncate instead of wrapping.

## 3. Compute table column widths at runtime
Remove every hardcoded width. In the handler for `tea.WindowSizeMsg`:

```go
func (m *model) layoutColumns(total int) {
	// Fixed columns: size to the widest header or value in the *current locale*.
	status := maxWidth(m.t("col.status"), m.statusLabels()...)
	due    := maxWidth(m.t("col.due"), m.sampleDates()...)
	prio   := maxWidth(m.t("col.priority"), m.priorityLabels()...)

	borders := 3 * 3 // separators between 4 cols
	title := total - status - due - prio - borders

	// Degrade in order instead of overflowing.
	switch {
	case title < 12:
		m.hidePriority = true // or swap to an icon-only column
		title += prio + 3
		fallthrough
	case title < 12:
		m.shortHeaders = true // use the "col.due.short" variants
	}
	m.cols = [...]int{title, status, due, prio}
}
```

- Give the task title column the leftover space. Fixed columns should be exactly as wide as their widest localized value.
- Decide now which columns to drop or shrink first at narrow widths. Don't wait to find out when German overflows.
- Shorten values instead of truncating them. For dates, use a short locale format (`13.10.`, `13.10.`, `10/13`). For status, use a single-cell symbol plus colour, or a translated short form.
- If you use `bubbles/table`, it takes fixed `Column.Width` values. Rebuild the columns on every resize. It also measures with lipgloss width, so wide characters are handled correctly.

## 4. Footer: let it drop hints by priority
- Use `bubbles/help` and set `m.help.Width = msg.Width`. When it runs out of space, the short view leaves off the remaining bindings and shows `…`. Order `ShortHelp()` so the essential bindings come first (quit, help, add, done).
- Make sure `?` (full help) is always reachable. It's the fallback for anything that got dropped.
- Keep key names separate from descriptions: `key.WithHelp("enter", t("help.open"))`. Translators should only see the description. Decide whether key names stay in English. Usually they should, because they match the labels on the keyboard.

## 5. Change the string catalog before you send it out
This is the part that's urgent before translators deliver.

- **Give each string a width budget.** Include a note such as "column header, max 8 cells at 60-col layout; Japanese chars count as 2". Translators can't guess this.
- **Ask for short variants** where space is tight: `col.due` / `col.due.short`, `help.delete` / `help.delete.short`. Getting these in the same delivery costs much less than a second round.
- **Don't build sentences by concatenation.** Use whole strings with named placeholders, because word order differs (Japanese is SOV). Use real plural rules via `go-i18n` or `golang.org/x/text/message`. Finnish has two plural forms, German has two, Japanese has one.
- **Format dates and numbers by locale**, not with `time.Format("Jan 2")`.

## 6. Test before the real strings arrive
- **Pseudo-localize now.** Add a fake locale that pads every string by about 40% and mixes in wide characters, e.g. `[Ｄüé Ｄáté ~~~]`. Run the app at 60 columns with it. Every overflow you find there will also happen with real German or Japanese.
- **Golden-file tests:** use `teatest` to render each locale (en, de, fi, ja, pseudo) at widths 60 and 80. Assert that no line exceeds the terminal width:
  ```go
  for _, line := range strings.Split(out, "\n") {
      if w := ansi.StringWidth(line); w > width { t.Errorf("line %d cells > %d", w, width) }
  }
  ```
- **Test real terminals with a CJK locale** (`LANG=ja_JP.UTF-8`) inside tmux, because of the ambiguous-width issue above.

## 7. Smaller checks
- **Japanese text input:** test typing through an input method (IME) in `textinput`/`textarea`. Cursor position and wide-character deletion have had bugs. Upgrade to the latest bubbles first.
- **Selection highlights:** if the highlight is a full-width background bar, pad it with `lipgloss.Width`-aware code. Otherwise Japanese rows will have a ragged edge.

If you only manage one thing before delivery, do #5: width budgets and short variants in the catalog. The code changes can wait for the strings to arrive. The catalog format can't.
