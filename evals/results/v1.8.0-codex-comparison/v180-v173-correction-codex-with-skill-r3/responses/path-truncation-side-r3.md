Use **start or middle truncation** for paths so the filename and extension survive. Cutting the end hides the most useful part.

For your 30-cell column:

```text
…/org.example.Viewer.desktop
/usr/…/org.example.Viewer.desktop
```

The first fits; the second is 33 cells, so it needs more space.

- Measure terminal **cells**, accounting for wide characters and combining marks. Reserve space for `…` or three cells for ASCII `...`; subtract padding and markers first.
- Keep each row on one line. Reveal the full path through a keyboard-accessible detail view.
- If every row shares `/usr/local/share/applications/`, show that directory once in the header and only filenames in rows. This removes 30 repeated cells per row.
- At 80×24, prioritize the file list over preview and metadata; at 60 columns, use a single-pane list. Below your tested usable minimum, show a clear “terminal too small” message.