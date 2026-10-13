Use **start or middle truncation**, so the filename and extension survive. Cutting the end would hide the part users need to identify the file.

For your 30-cell column:

```text
…/org.example.Viewer.desktop
/usr/…/org.example.Viewer.desktop
```

The first fits in 28 cells; the second needs 33, so choose the first here.

- Measure terminal **cells**, accounting for Unicode width; reserve space for `…` or three cells for `...`.
- Keep each file on one row. Provide a keyboard-accessible detail view showing the full path.
- If rows share a directory, show it once in the header and list filenames—repeated prefixes waste space.
- At 80×24, drop optional previews or metadata first; at 60 columns, use a single file pane. Below your tested usable minimum, show a clear “terminal too small” message.