No—**truncate paths at the start or middle so the filename survives.** Cutting the end hides the part users need to identify the file.

For your 30-cell column, use:

```text
…/org.example.Viewer.desktop
```

If the root matters, this fits exactly in 30 cells when `…` occupies one cell:

```text
/usr/…/org.example.Viewer.desktop
```

Measure **terminal display cells**, including the ellipsis, padding, and selection marker. Preserve Unicode grapheme boundaries; reserve three cells for an ASCII `...` fallback. Keep rows unwrapped and expose the full path through a keyboard-accessible detail view.

If every row shares a directory, show that directory once above the list and display filenames only. Repeating this example’s 30-cell directory prefix spends the entire column on shared context.

At 80×24, prioritize the file list and hide secondary columns as needed; in a 60-column split, use a single-pane list with details on demand. Show “terminal too small” only below the minimum needed to operate that view.