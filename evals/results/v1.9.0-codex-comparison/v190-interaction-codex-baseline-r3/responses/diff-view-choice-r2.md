Use **unified diffs at 100 columns** and **side-by-side diffs at 160 columns**, based on the width available to the diff pane.

| | 100 columns | 160 columns |
|---|---|---|
| Default view | Unified: removals followed by additions | Side by side: old left, new right |
| Navigation | File list opens as an overlay | Optional file sidebar; hide it if panes get cramped |
| Line numbers | Old/new numbers in a compact gutter | One number gutter per pane |
| Long lines | Horizontal scrolling; wrap toggle | Synchronized horizontal scrolling; wrap toggle |
| Context | 3 lines, with expandable gaps | Same, aligned across panes |

**100 columns — unified**
```text
src/config.ts · 1 of 4 files                                  +2 −1
──────────────────────────────────────────────────────────────────
@@ loadConfig() @@
  41  41    const config = readConfig(path);
  42     − return config;
      42 + validateConfig(config);
      43 + return normalizeConfig(config);

        ⋯ 18 unchanged lines · Enter to expand
```

**160 columns — side by side**
```text
src/config.ts · 1 of 4 files                                                        +2 −1
────────────────────────────────────────────────────────────────────────────────────────
 OLD                                        │ NEW
 41   const config = readConfig(path);      │ 41   const config = readConfig(path);
 42 − return config;                       │ 42 + validateConfig(config);
                                           │ 43 + return normalizeConfig(config);
```

Switch to side by side only when **each pane has at least 60 columns of code space**, after gutters, borders, and sidebars. Allow a manual override and preserve the focused hunk when resizing.

Keep `+`/`−` markers alongside color, highlight changed words within modified lines, and show a clear indicator when content extends offscreen. A compact footer can expose: `j/k scroll · [/ ] hunk · Tab files · v view · w wrap`.