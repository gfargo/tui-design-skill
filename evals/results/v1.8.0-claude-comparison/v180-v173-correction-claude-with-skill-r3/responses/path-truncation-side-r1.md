No. Cutting the end is the worst choice for paths. At 30 cells, tail truncation gives you:

```
/usr/local/share/applicatio…
```

The filename is gone. Every `.desktop` file in that directory now renders as the same row, so the list can't tell them apart.

**Cut from the start instead and keep the filename:**

```
…/org.example.Viewer.desktop      (28 cells)
```

### How to do it

1. **Cut at a `/` boundary, not at an exact character count.** A strict 29-character cut produces `…ns/org.example.Viewer.desktop`, and the `ns/` fragment is noise. Drop whole leading path segments until the rest fits, then prepend `…`.
2. **Middle truncation (`/usr/…/file`) only works when there's room.** It's useful when the root matters, such as telling `/usr` apart from `/home`. Here it needs `/usr/…/org.example.Viewer.desktop`, which is 33 cells and doesn't fit. Try middle first if you like, and fall back to start truncation.
3. **If the filename alone is too wide, keep the extension.** Truncate inside the name: `org.example.Very…iewer.desktop`. The extension and the distinctive tail usually matter most.
4. **Leave a cell for the `…`**, and don't cut so far that only `…/` is left.
5. **Measure terminal cell width, not string length.** CJK characters and emoji take 2 cells. Combining marks take 0. A `len()`-based cut will misalign the column or split a character.
6. **Show the full path somewhere.** Use a status line, a preview header, or a detail view on Enter for the selected row, so the cut never hides information.

### Other options for a file list

- **Show paths relative to the current or common root.** If every entry is under `/usr/local/share/applications/`, show that prefix once in the panel title and list only the filenames. This often fixes the overflow without cutting anything.
- **If the column can resize, recompute on resize** rather than storing truncated strings.

Rule of thumb: cut paths from the start or middle so the filename survives. Cut prose, names and IDs from the end, because their beginning carries the meaning.
