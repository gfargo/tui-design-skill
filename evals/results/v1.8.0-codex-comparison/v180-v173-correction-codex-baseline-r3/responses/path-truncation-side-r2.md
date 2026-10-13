Prefer **middle truncation** so the filename stays recognizable. Cutting the end hides the part users usually need most.

For a 30-cell column:

```text
/usr/…g.example.Viewer.desktop
```

If the directory is already shown elsewhere, display just the basename:

```text
org.example.Viewer.desktop
```

Measure terminal **display cells**, not string length, and include the ellipsis in that budget. Let users reveal the full path on selection or in a details pane.