I wouldn't cut the end. In a file path the end usually tells you the most, and here cutting the end removes the filename completely:

```
/usr/local/share/applications…     ← 30 cells, but which file is it?
```

That path is 56 cells long. The first 30 are `/usr/local/share/applications/`, so cutting the end leaves only the directory.

## Shorten from the left or middle instead

Shorten the parts in this order:

1. **Keep the filename whole if it fits.** Use whatever width is left for the start of the directory, and replace the middle with `…`:
   ```
   /…/org.example.Viewer.desktop      ← 30 cells
   /usr/local/…/org.example.Viewer.desktop   ← same path at 40 cells
   ```
   Keeping the leading `/` (or `~`) shows whether the path is absolute or relative to home.

2. **If the filename alone is too wide, cut the middle of the filename.** Keep its start and its extension:
   ```
   …/org.exampl…Viewer.desktop
   ```
   The start and the extension are usually what tell similar files in the same directory apart, so keep both.

3. **Fall back to a plain left cut (`…ewer.desktop`)** only if the column is very narrow.

## Details that matter

- **Measure in cells, not characters or bytes.** CJK characters and many emoji take 2 cells, and combining marks take 0. Use `wcwidth`/`wcswidth` or your toolkit's equivalent. Never cut in the middle of a wide character or a grapheme cluster.
- **`…` is one cell.** If the terminal or locale isn't UTF-8, fall back to `...` (3 cells) and adjust your sums.
- **Show the full path somewhere.** For example, put it in a status line or footer for the selected row, or show it on hover or focus. Any shortened view loses information, so give users a way to see the whole path.
- **Consider grouping by directory.** If many rows share a parent, a tree or a directory header can save more space than any shortening rule. Then the column only needs to show filenames.

## Sketch

```python
from wcwidth import wcswidth

def fit_path(path, width, ell="…"):
    if wcswidth(path) <= width:
        return path
    head, _, base = path.rpartition("/")
    # 1. Filename whole, directory shortened in the middle
    prefix = "/" if path.startswith("/") else ("~" if path.startswith("~") else "")
    tail = "/" + base
    room = width - wcswidth(tail) - wcswidth(ell)
    if room >= wcswidth(prefix):
        return take_left(head, room) + ell + tail   # take_left: longest prefix with width <= room
    # 2. Filename alone too wide: cut its middle, keep the extension
    return middle_truncate(base, width, ell)
```

(`take_left` and `middle_truncate` should step through grapheme clusters and add up cell widths. Don't slice the string by index.)

**Recommendation:** keep the filename whole, put the `…` in the directory part, and show the full path for the selected row.
