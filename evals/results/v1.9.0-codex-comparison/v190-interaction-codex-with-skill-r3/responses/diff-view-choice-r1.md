**Use unified diffs at 100 columns and side-by-side diffs at 160.** Base the switch on the diff pane’s available width after subtracting sidebars and borders.

| Available width | Default layout |
|---|---|
| 100 columns | Unified: removals followed by additions |
| 160 columns | Side-by-side: old left, new right |
| Below ~120 columns | Fall back to unified |

For side-by-side, require at least **55 columns per side plus a 2-cell separator**. At 160 columns without a sidebar, each side gets 79 cells, including its line-number and change-marker gutters.

Compact sketches—the real panes fill the available width:

```text
100 columns: unified
src/config.ts                         Hunk 1/3
@@ -40,3 +40,3 @@
  40 40   const config = {
- 41        timeout: 1000,
+    41     timeout: 5000,
  42 42   };

[ prev hunk  ] next hunk  / search  ? help
```

```text
160 columns: side-by-side
src/config.ts                                      Hunk 1/3
Old                             | New
  40   const config = {          |   40   const config = {
- 41     timeout: 1000,          | + 41     timeout: 5000,
  42   };                       |   42   };

[ prev hunk  ] next hunk  / search  ? help
```

Keep these behaviors consistent:

- Preserve `+`/`-` markers and line numbers; red/green should only reinforce meaning. Highlight changed words within changed lines.
- Don’t wrap side-by-side lines. Indicate clipped content and provide horizontal scrolling, preferably synchronized between sides.
- On resize, preserve the current file, hunk, and selected source line.
- Offer an explicit unified-view toggle even on wide terminals.

Pressure-test the smaller sizes too:

```text
60-column fallback                 160-column layout
src/config.ts  Hunk 1/3             Old                | New
- 41     timeout: 1000,             - 41 timeout: 1000, | + 41 timeout: 5000,
+    41  timeout: 5000,
[ prev  ] next  ? help
```

At **80×24**, use full-width unified mode and hide the file sidebar behind a file picker. At **60 columns**, retain unified mode, shorten paths while preserving filenames, and reduce footer hints. A reasonable proposed hard minimum is **40×8**; below it, show the required dimensions and keep quit working.

For clutter: use **zero nested borders**, one central separator in split mode, and no repeated file path on every row. Change state needs only two signals: its marker and optional color. With four-digit line numbers, unified gutters consume about 12% of a 100-column row; split gutters plus separation consume about 10% at 160. Keep the rest for code.