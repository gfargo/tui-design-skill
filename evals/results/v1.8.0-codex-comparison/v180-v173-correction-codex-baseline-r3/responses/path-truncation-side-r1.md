Prefer **middle truncation** for paths: preserve the root and filename, since the filename usually matters most.

For a 30-cell column:
```text
/usr/…/example.Viewer.desktop
```

If the filename alone is too long, truncate its stem while preserving the extension. Show the full path on focus or in a details pane.

Measure **terminal display cells**, not string length—Unicode characters can occupy zero, one, or two cells.