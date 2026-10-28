**Use unified diffs at 100 columns and side-by-side diffs at 160.** Switch based on the diff pane’s available width, after subtracting sidebars and chrome.

| Available width | Default |
|---|---|
| 100 columns | Unified: removals followed by additions |
| 160 columns | Side-by-side: old left, new right |
| Around 120 columns | Switch only if each side retains at least 55 columns, plus a 2-cell separator |

Compact sketches; panes expand to the available width:

```text
100 columns — unified
src/config.ts                         hunk 1/3
@@ retry policy @@
  OLD NEW
-  42      const retries = 3;
+      42  const retries = 5;
   43  43  connect(retries);

[ previous hunk  ] next hunk  / search  ? help
```

```text
160 columns — side-by-side
src/config.ts                                      hunk 1/3
OLD                         | NEW
- 42 const retries = 3;      | + 42 const retries = 5;
  43 connect(retries);       |   43 connect(retries);

[ previous hunk  ] next hunk  / search  ? help
```

Keep these behaviors consistent:

- Preserve `+`/`-` markers and line numbers; red/green reinforces meaning. Highlight changed words within changed lines.
- Align corresponding lines in split mode, leaving blanks for unmatched additions or deletions.
- Don’t wrap split lines. Show a clipping indicator and allow horizontal scrolling; keep line-number gutters fixed.
- Provide `Auto / Unified / Split` selection. On resize, preserve the current file, hunk, and selected source line.
- Make file navigation a picker or drill-down when it would steal necessary diff width.

At **80×24**, use full-width unified mode with a compact footer. At **60 columns**, keep the same single-pane model, shorten paths, and hide optional metadata:

```text
60-column fallback              Wide fallback above: split
.../config.ts  hunk 1/3
- 42     const retries = 3;
+     42 const retries = 5;
[ prev  ] next  ? help
```

A reasonable proposed minimum is **40×10**; below it, show “Terminal too small: need 40×10,” while keeping quit working.

For the clutter audit: use **zero nested borders**, one separator in split mode, and no marker on every context row. Encode additions/deletions with at most **a sign plus color**. With two chrome rows in a 24-row terminal, roughly **8% of rows** go to chrome; remove outer frames, per-hunk boxes, and repeated filenames.