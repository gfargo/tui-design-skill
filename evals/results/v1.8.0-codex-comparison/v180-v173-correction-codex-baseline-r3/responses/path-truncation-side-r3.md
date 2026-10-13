Prefer **middle truncation** for paths: keep the root and filename, since the filename usually matters most.

For a 30-cell column:
```text
/usr/…g.example.Viewer.desktop
```

If the directory context isn’t useful, show just the filename:
```text
org.example.Viewer.desktop
```

Measure terminal **display cells**, not character count, and provide the full path on focus or in a details pane.