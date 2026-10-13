No. Cutting the end is the worst choice for paths, because the end holds the filename, which is the part people need to read. With a 30-cell column, end-truncation gives you:

```
/usr/local/share/applications…
```

That's 30 cells, and every row under that directory looks the same. Truncate from the left instead and keep the basename whole:

```
…/org.example.Viewer.desktop      (28 cells)
```

**A rule that holds up:**

1. **The whole path fits:** show it unchanged.
2. **Otherwise, drop leading directories** one at a time until it fits, and prefix `…/`. Keep as many parent directories as the width allows, e.g. `…/applications/foo.desktop`.
3. **The basename alone is too long:** cut the middle of the name and keep the extension, e.g. `org.exampl…Viewer.desktop`. The start and the extension are the parts people recognize.
4. **Duplicate names in view:** if two rows would both show `…/config.toml`, keep enough parent directories to tell them apart (`…/foo/config.toml` vs `…/bar/config.toml`).

**Details people often miss:**

- **Measure display width, not string length.** Use `wcwidth`, or your toolkit's equivalent. CJK characters and emoji take 2 cells, and `…` (U+2026) takes 1. If the terminal or font might not render it, fall back to `...`.
- **Show the full path somewhere else.** For example, put the selected row's full path in a status line or footer, so truncation never hides information completely.
- **Consider the column's context.** If the list is always inside a known root (a project directory, say), show paths relative to that root before truncating anything. That often removes the need to truncate at all.
- **Avoid fish-style abbreviation here.** `/u/l/s/a/org.example.Viewer.desktop` is still 35 cells, and it's harder to read than `…/`.
