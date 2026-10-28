**Pick the diff mode from the width of the diff pane, not the terminal.** On 100 columns, show a **unified** diff across the full width. On 160 columns, show a **side-by-side** diff. Use side-by-side only when each side gets at least 55 columns plus a 2-column gutter between them, so the diff pane needs 112 columns or more. Otherwise use unified. This rule comes from `references/visual-patterns.md` → *Diff views* and the breakpoint ladder.

Using the pane width means a sidebar can't silently squeeze side-by-side below what's readable. If the user opens the file list at 140 columns and the diff pane drops under 112, it switches to unified.

## 160 columns: side-by-side

```
 src/server/routes.go                               +12 -4   hunk 2/5
 41   func handle(w, r) {                    │ 41   func handle(w, r) {
 42 - │ id := r.URL.Query().Get("id")        │ 42 + │ id, err := parseID(r)
                                             │ 43 + │ if err != nil {
                                             │ 44 + │   return badRequest(w, err)
                                             │ 45 + │ }
 43   │ user := store.Get(id)                │ 46   │ user := store.Get(id)
 @@ -58,6 +61,8 @@ func list(...)            │
 ...
 ]/[ hunk  }/{ file  s unified  f files  ←/→ scroll  ? help
```

- Each side gets about 78 columns: a 4-column line number, the `+`/`-` marker, a space, and about 72 columns of code.
- Leave blank filler rows across from added or removed lines so the two sides stay row-aligned. Don't decorate the filler rows.
- Don't wrap lines. Truncate them with `…` and scroll both sides horizontally together.
- The file list starts hidden and `f` opens it. With a 28-column list open, the diff pane is about 131 columns, which still fits side-by-side, but each side drops to about 57 columns of code. That's why it starts hidden.

## 100 columns: unified

```
 src/server/routes.go                               +12 -4   hunk 2/5
  41  41   func handle(w, r) {
  42     - │ id := r.URL.Query().Get("id")
      42 + │ id, err := parseID(r)
      43 + │ if err != nil {
      44 + │   return badRequest(w, err)
      45 + │ }
  43  46   │ user := store.Get(id)
 @@ -58,6 +61,8 @@ func list(...)
 ]/[ hunk  }/{ file  s split  f files  ? help
```

- Use two line-number columns (old and new) and one marker column. That leaves about 88 columns for code, which is more than one side gets at 160.
- If the file list is open, it shows as an overlay or a narrow pane. Its width comes out of the code area, not out of the gutters.

## Rules for both widths

- **Markers carry the meaning:** `+` or `-` in a fixed column, with red/green on top. Context lines get a space. Inside a changed line, highlight the words that changed: a stronger background in color, underline or reverse under `NO_COLOR`.
- **Manual override:** `s` switches between unified and split, and the choice is remembered. If a forced split no longer fits after a resize, fall back to unified and say so in the status line, e.g. `split needs 112 cols`. Don't render a squashed split.
- **Navigation:** `]`/`[` move between hunks, `}`/`{` between files, and the header shows `hunk 2/5`.
- **Rendering:** measure cell width, not string length. Tabs, CJK and emoji in code will otherwise break the alignment. Virtualize the rows, because large diffs can run to tens of thousands of lines.

## Clutter audit

- **Borders:** no box around the diff pane. The only line in the diff is the single `│` between the two sides.
- **Signals for added/removed:** two, the marker and its color. Don't also add `[+]` badges, icons, or a full-row background on top of the word highlights.
- **Markers on every row:** none. Context lines carry no glyph.
- **Hunk headers:** one dim line. No extra separators or blank rows around them.

## The floor (60 columns, too small, plain mode)

```
 routes.go                 +12 -4  2/5
  42 - │ id := r.URL.Query().Get("…
  42 + │ id, err := parseID(r)
  43 + │ if err != nil {
 ]/[ hunk  f files  ? help
```

- **80×24:** the same as the 100-column layout with about 68 columns of code. The file list is overlay-only.
- **60 columns (a tmux split):** unified only, with the new line number only. Shorten the file path from the start so the filename survives, and shorten the footer to the essential keys.
- **Too small:** below your tested minimum (for example 40×8), show "Terminal too small — needs 40×8". Don't draw a garbled diff.
- **No terminal or plain mode:** output a standard unified diff, so it pipes to `patch`, `less` or `delta`.

## Testing

Add golden-frame tests at 160, 120, 111 (the first width that must fall back to unified), 100, 80, 60 columns and the minimum, each with and without `NO_COLOR`. The lazygit entry in `references/exemplar-apps.md` is a good example of a persistent file list next to a large diff panel.

If you tell me the framework (Bubble Tea, Ratatui, Textual or Ink), I can show how to measure the pane width and switch modes in its layout system.
