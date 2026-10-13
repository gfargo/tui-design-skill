There's no code in the working directory, so this advice is based on how Bubble Tea and Lip Gloss usually behave rather than on your implementation. Before translators start, the main job is to stop sizing the layout around English text and start sizing it around the terminal width and what each string actually measures on screen.

## 1. Measure display width, not string length
- Japanese characters take **2 terminal columns** each. `len()` counts bytes and `utf8.RuneCountInString` counts characters, so neither gives you screen width. Use `lipgloss.Width()` or `ansi.StringWidth()` from `charmbracelet/x/ansi` everywhere you pad, align or truncate.
- Search for `len(`, `%-20s` and `fmt.Sprintf` with width verbs that touch text the user sees. `%-20s` pads by character count, so Japanese columns will be misaligned.
- Some symbols (`●`, `★`, `…`, `→`, some box-drawing characters) have "ambiguous" width. Terminals and tmux disagree on whether they take 1 or 2 columns, and that breaks borders. Use plain ASCII markers, or test the symbols in tmux with CJK settings turned on.

## 2. Truncate by grapheme and display width
- Use `ansi.Truncate(s, w, "…")`, never `s[:n]`. Byte slicing can cut a multi-byte character in half. Width-unaware truncation can also leave half of a 2-column character, which pushes the border one column too far.
- Combined characters like `ä` must stay together; the `x/ansi` functions handle this.

## 3. Make the table respond to width
At 60 columns, borders, padding and 3 separators leave roughly 50 columns of content for 4 columns. German and Finnish text often runs 30–50% longer than English.
- Recompute column widths on every `tea.WindowSizeMsg`. Don't hardcode them.
- Give each column a minimum width, a priority and a flex weight. Let the title column absorb the remaining space and truncate first.
- Set breakpoints. For example, below about 70 columns, drop or merge the lowest-priority column (show due date as a compact `10/13`, or move status into a one-character glyph).
- Calculate header widths from the **translated** header text. German "Fälligkeitsdatum" and Finnish "Määräpäivämäärä" are much longer than "Due". Ask translators for a **short header variant** as well as the full one.
- Wrapping is a problem in both directions. Lip Gloss wraps on spaces, so Japanese text (which has no spaces) may not break where you want it to. German and Finnish compound words are long and can't be hyphenated. In table cells, truncate to one line instead of wrapping.

## 4. Footer key hints
- Use `bubbles/help` with a `key.Map`, and set `help.Width` on resize. It drops bindings that don't fit and adds an ellipsis.
- Order `ShortHelp()` by importance so that the items dropped at 60 columns are the ones that matter least.
- Keep the **key** untranslated (`q`, `enter`, `/`) and translate only the **description**. Ask for terse verbs ("Beenden", "Lopeta", "終了"). Make sure `?` for the full help is always visible.

## 5. String structure (fix before translation starts)
- Don't build sentences by joining pieces (`"Deleted " + n + " tasks"`). Word order differs across these languages. Use whole messages with named placeholders, for example with `go-i18n` or `golang.org/x/text/message`.
- Pluralization follows each language's own rules (from the CLDR standard). Japanese has no plural forms and Finnish has two. Don't hardcode `if n == 1`.
- Format dates, numbers and relative times ("in 2 days") per locale. Don't put English format strings in the code.
- Sort Finnish text with locale rules (`golang.org/x/text/collate`). Finnish sorts `å ä ö` after `z`.
- Give every string a stable ID and a context comment for translators: "table header, max 10 columns; Japanese characters count as 2."

## 6. Test before strings arrive
- **Pseudo-localization:** add a fake locale that pads every string by about 40% and mixes in accented and full-width characters, such as `[Ðüé Ðåţé ｘｘ]`. Run it at 60 and 80 columns now and fix whatever breaks.
- Add golden-file tests (`teatest`) at widths 60, 80 and something narrow like 40, for each locale. Check that no line exceeds the terminal width as measured by `ansi.StringWidth`.
- Test Japanese text entry with an input method in tmux. Check that the `textinput` cursor lands in the right place with 2-column characters.

## Translator brief
Give translators a width budget for each string (in terminal columns, noting that Japanese characters count as 2), screenshots at 60 columns, and a request for short variants of headers and footer hints. That costs much less than fixing overflow after delivery.
