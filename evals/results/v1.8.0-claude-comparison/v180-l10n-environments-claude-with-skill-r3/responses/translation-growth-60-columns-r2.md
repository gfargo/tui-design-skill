I'd make one change first: stop sizing anything from English text. Measure each column and footer hint from the rendered translated text at the current width, give the layout a defined fallback at 60 columns, and test it with a pseudo-locale this week. You'll find most of the breakage before the translators deliver.

## 1. What breaks and why

- **German and Finnish are long, and they make long words you can't break.** Short strings grow the most: IBM budgets 100–200% extra for strings under 10 characters. Your column headers and footer hints are exactly those strings. For example, "Due" (3 cells) becomes "Fälligkeitsdatum" (16) or "Määräpäivä" (10). Status values grow too: "In progress" becomes "In Bearbeitung" (14).
- **Japanese is short in characters but wide on screen.** 期限 is 2 characters but takes 4 cells. Any code that uses `len()` or counts runes will misalign it. Only `lipgloss.Width()` gives the true width.
- **Some common symbols change width in Japanese setups.** `…`, `·`, `•`, `←↑→↓` and the rounded border corners are "ambiguous width": 1 cell in most terminals, 2 when a Japanese user turns on the terminal's ambiguous-wide setting. The default separator in `bubbles/help` is ` • `, and the usual key labels like `↑/k` use arrows. So the footer and borders can drift by a few cells only for Japanese users.

## 2. Code changes to make now

**Table**
- **Work out column widths at runtime.** For each column, take the wider of the translated header and the data, then clamp it. Status is a fixed set of values, so measure every translated status value once at startup and use the widest.
- **Rank the columns and decide what each width band shows.** I'm guessing your columns are Title / Status / Due / Owner, so adjust this to the real ones:
  - **≥80 columns:** all four.
  - **60–79 columns:** drop Owner, and Enter opens a detail view with every field.
  - **Below about 60 columns:** Title plus a short status code, with no full status word.
  - **Below your stated minimum:** a translated "terminal too small — need 40×10". That message has to fit at the minimum width in every language too.
- **Title is the column that flexes.** It gets whatever width is left over and is cut off at the end with an ellipsis, never wrapped. Headers get cut before data does, and the full header text goes in the `?` help screen.
- **Cut table borders.** A bordered 4-column table with `Padding(0,1)` uses 13 of your 60 cells on borders and padding. Two-space gaps instead use 6. That frees 7 cells, which covers most of the German growth in a single header.
- **Keep dates as ISO-8601** (`2026-10-13`, or `10-13` when narrow). They are 10 cells in every language and sort correctly. Use the locale's formatting only in prose and the detail view.

**Footer**
- **Build it from `key.Binding` through `bubbles/help`, and set `help.Width = m.width`** on every `WindowSizeMsg`. When space runs out, `help` stops at the first hint that doesn't fit and appends an ellipsis. Order `ShortHelp()` by importance and keep it to 3–5 bindings.
- **Keep `? help` visible.** It's typically the last hint, so it gets dropped first. Either draw `? help` yourself, right-aligned, and fill the rest of the line from the keymap, or put it first.
- **Only the action words get translated, never the keys.** `q`, `/` and `?` stay the same in every language. Translators should only see the `WithHelp` description.
- **Replace the ambiguous-width separator** (`help.ShortSeparator`) with two spaces or ` | `, unless you test with the ambiguous-wide setting turned on.

**Strings**
- **Use whole-sentence messages with placeholders, never joined fragments.** `"Delete " + name + "?"` breaks in Japanese, which puts the verb last, and in Finnish, which changes word endings by case.
- **Handle plurals with the library's plural support** (`golang.org/x/text/message` or go-i18n). German and Finnish have two plural forms, and Japanese doesn't change the word at all.
- **Give translators short and long versions for constrained strings,** like `header.due.short` and `header.due`, along with a width limit in *cells*. Ask for the short forms in this first round, not after the layout breaks.
- **Check whether you mix two width libraries.** go-runewidth treats ambiguous characters as wide under any `ja` locale, while lipgloss v2 treats them as narrow. If anything in your stack still uses go-runewidth (Bubbles v1's table does, for example), Japanese rows can misalign against lipgloss-measured borders.

## 3. Test before translations arrive

1. **Make a pseudo-locale** where every string is about 50% longer, wrapped in markers (`[!! Fäällîgkéît !!]`). Make a second one that uses fullwidth characters so you exercise 2-cell text.
2. **Golden-test the frames** with teatest/v2 for {en, pseudo-long, pseudo-wide} × {80×24, 60×24, your minimum}. Pin the color profile with `tea.WithColorProfile(colorprofile.ASCII)` and pin the locale. When the real translations arrive, add de/fi/ja to the same set.
3. **Test resizing:** send `tea.WindowSizeMsg{Width: 60}` in the middle of a run and check that the columns rearrange.
4. **Check it by eye once** in a `tmux split-window -h` and once in a terminal with ambiguous-wide turned on.

If the pseudo-locale goldens look right at 60 columns, the real German, Finnish and Japanese strings should fit without layout changes.
