Use **unified diffs at 100 columns** and **side-by-side diffs at 160 columns**, with a manual toggle for either layout.

| | 100-column terminal | 160-column terminal |
|---|---|---|
| Default layout | Unified: removed and added lines stacked | Side by side: old left, new right |
| File navigation | Collapsed; open as an overlay | Optional sidebar, about 24 columns |
| Line numbers | Old and new numbers in one gutter | One number gutter per pane |
| Long lines | Horizontal scrolling | Synchronized horizontal scrolling |
| Context | 3 lines around each change; expandable | Same |

At **100 columns**, preserve space for code:

```text
src/config.ts                              1 of 4 files  +2 −1
────────────────────────────────────────────────────────────
@@ loadConfig
  41  41   const config = {
  42     −   timeout: 1000,
      42 +   timeout: 5000,
      43 +   retries: 3,
  43  44   };
```

At **160 columns**, make comparison immediate:

```text
src/config.ts                                      1 of 4 files  +2 −1
──────────────────────────────────┬──────────────────────────────────
 OLD                              │ NEW
 41   const config = {            │ 41   const config = {
 42 −   timeout: 1000,             │ 42 +   timeout: 5000,
                                  │ 43 +   retries: 3,
 43   };                          │ 44   };
```

Choose the layout based on **available diff width**, after subtracting navigation and borders. Switch to side by side when each code pane can retain roughly **60 columns**; collapse the sidebar before sacrificing that space.

Keep these behaviors consistent:

- Highlight changed words within changed lines.
- Use `−` and `+` alongside color so changes remain readable without it.
- Preserve the selected file, hunk, and line when resizing.
- Default to no wrapping; offer a wrap toggle for prose and long lines.
- Keep file and hunk navigation visible in a compact footer, such as `Tab files · [/] hunk · v layout · w wrap`.