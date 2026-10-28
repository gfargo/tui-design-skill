The directory is empty, so this advice isn't tied to your code. **My recommendation: use a unified diff at 100 columns and a side-by-side diff at 160 columns.** Pick the layout from the width each code pane would actually get, not from a fixed column count.

## Why the split happens between those two widths

Count the space the chrome takes: line numbers (about 4 + 1 per side), the `+`/`-` sign column (2 per side) and a divider (1). That's roughly 15 columns.

| Width | Side-by-side code per pane | Unified code width |
|---|---|---|
| 100 | ~42 cols, too cramped, most lines wrap | ~89 cols, comfortable |
| 160 | ~72 cols, comfortable | ~149 cols, mostly empty space |

Rule: **use side-by-side only if each pane gets at least ~70 columns of code**, which works out to a terminal width of about 150 or more. Recompute this on every resize (SIGWINCH), and add a key such as `s` to override the automatic choice.

## 100 columns: unified

```
 src/parser.rs  +12 −4                                         [unified · s: split]
 @@ -40,7 +40,9 @@ fn parse_header
  40   40 │   let mut buf = String::new();
  41      │ - let n = reader.read_line(&mut buf)?;
       41 │ + let n = reader
       42 │ +     .read_line(&mut buf)
       43 │ +     .context("reading header")?;
  42   44 │   if n == 0 {
```

- Show both old and new line numbers in the gutter.
- Use soft-wrap with a `↪` marker in the gutter. Don't truncate, because truncation hides changes.
- Highlight the changed words within a line (a brighter background on the changed span), not just the whole line.

## 160 columns: side-by-side

```
 src/parser.rs  +12 −4                                                                          [split · s: unified]
  40 │   let mut buf = String::new();                     │  40 │   let mut buf = String::new();
  41 │ - let n = reader.read_line(&mut buf)?;             │  41 │ + let n = reader
     │                                                   │  42 │ +     .read_line(&mut buf)
     │                                                   │  43 │ +     .context("reading header")?;
  42 │   if n == 0 {                                     │  44 │   if n == 0 {
```

- Line the hunks up by inserting blank filler rows (shown dim or hatched) on the shorter side, so matching lines stay on the same row.
- Scroll both panes together, vertically and horizontally.
- Wrapped lines have to stay row-aligned too. Pad the other side so a wrapped line never pushes the two panes out of sync.

## Rules for both layouts

- **Don't rely on color alone.** Always show the `+`/`-` signs, for colorblind users, `NO_COLOR` and monochrome terminals.
- **Measure display width, not bytes or characters.** Use `wcwidth`/`unicode-width` so CJK text and emoji don't break alignment. Expand tabs to a fixed width (4 or 8) before measuring.
- **File list sidebar:** at 160 a ~30-column file list leaves about 130 columns, so each split pane gets only ~57. Either use unified next to an open sidebar, or make the sidebar collapsible (`Tab`) and use side-by-side when it's hidden. At 100 columns, show the file list as an overlay or picker instead of a permanent pane.
- **Hunk headers:** keep the `@@` line and the function context, and add "N unchanged lines" fold markers that expand.
- **Header bar:** show the current mode and the toggle key so the automatic switch doesn't surprise people.

If you tell me your framework (Ratatui, Bubble Tea, Textual, Ink, etc.), I can sketch the layout-selection and alignment code.
