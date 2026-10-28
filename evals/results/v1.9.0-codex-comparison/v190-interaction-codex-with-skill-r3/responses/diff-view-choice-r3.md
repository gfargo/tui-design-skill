**Use a unified diff at 100 columns and side-by-side at 160.** Switch based on the diff pane’s available width, after subtracting any sidebar.

Assuming a full-screen review workflow, let the diff take priority; open the file list on demand.

| Available width | Default layout | Behavior |
|---|---|---|
| 160 columns | Side-by-side | Old left, new right; synchronized vertical scrolling |
| 120+ columns | Side-by-side if it fits | Each side needs at least 55 columns plus a 2-cell central gutter |
| 100 columns | Unified | Removed lines followed by added lines; both line numbers retained |
| 80×24 | Unified, full width | Hide the sidebar and secondary metadata; keep one compact footer |
| 60 columns | Unified, single pane | Shorten paths; file navigation becomes a separate view |

Sketches below are abbreviated horizontally; actual panes fill the available width.

```text
100 columns — unified
src/config.go   +1 -1   hunk 1/3                 Unified
    OLD NEW
     41  41   func configure() {
-    42          timeout = 10
+        42      timeout = 30
     43  43   }

[ prev hunk | ] next hunk | v layout | / search | ? help
```

```text
160 columns — side-by-side
src/config.go   +1 -1   hunk 1/3            Side-by-side
OLD                       | NEW
 41   func configure() {  |  41   func configure() {
 42 -     timeout = 10     |  42 +     timeout = 30
 43   }                   |  43   }

[ prev hunk | ] next hunk | v layout | / search | ? help
```

```text
60 columns — unified fallback
.../config.go   hunk 1/3
    OLD NEW
-    42          timeout = 10
+        42      timeout = 30

[ previous | ] next | ? help
```

Keep these behaviors consistent:

- **Long lines:** don’t wrap side-by-side. Show a right-edge overflow marker and support horizontal scrolling with line numbers pinned. Use the same default in unified mode; optional wrapping can help with prose.
- **Change emphasis:** retain `+`/`-` markers in monochrome. Use red/green as reinforcement and emphasize changed words within each line.
- **Navigation:** provide previous/next hunk, scrolling, search, file selection, layout toggle, and help. Preserve the current file, hunk, and source-line position across resizing.
- **Layout choice:** offer `Auto / Unified / Split`. If split cannot meet its minimum width, temporarily show unified and explain this in the status line.
- **States:** show “Loading diff…”, “No changes”, or “Couldn’t load diff — r retry” within the same content area.

For clutter, use **zero enclosing borders**, one central separator in split view, and no repeated file paths on individual rows. With five-digit line numbers, unified gutters consume about 14% of a 100-column row; split gutters and the separator consume about 11% at 160. Avoid spending more on decorative boxes.

A reasonable initial minimum is **40×10**, to validate with rendered frames. Below that, show “Terminal too small: need 40×10” while keeping quit available. Also offer plain unified output for noninteractive and accessibility use.