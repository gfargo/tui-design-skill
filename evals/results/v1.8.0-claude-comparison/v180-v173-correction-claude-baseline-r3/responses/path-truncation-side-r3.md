I'd avoid cutting the end. In a file list, the most useful part of a path is usually the end: the filename. If you cut at 30 cells you get:

```
/usr/local/share/applications…
```

Every file in that directory now shows the same text, so the column can't tell them apart. Keep the end and shorten from the left or the middle instead.

**Fallback order, tried until the path fits:**

1. **Show the full path** if it fits.
2. **Shorten the directory names** to their first letter, fish-shell style: `/u/l/s/a/org.example.Viewer.desktop`. That's 35 cells, which is still too long here, but it often fits for shorter names.
3. **Drop leading directories** and replace them with `…/`. Keep as many of the closest parent directories as fit:
   ```
   …/org.example.Viewer.desktop      (28 cells)
   …/applications/foo.desktop        (keeps the parent when there's room)
   ```
4. **Shorten the filename in the middle** if the name alone is too long, keeping the start and the extension:
   ```
   org.example.Vi…Viewer.desktop
   ```

**Details that matter:**

- **Measure display cells, not characters.** CJK characters and emoji are 2 cells wide, and combining marks are 0. Use `wcwidth` or your toolkit's equivalent, or wide names will break the column alignment.
- **Use the single `…` character** (1 cell) rather than `...` (3 cells). Fall back to `...` only if you need plain ASCII output.
- **Show the full path somewhere.** Put the untruncated path of the focused row in a status bar or footer. Shortening the list is only acceptable if the full path is one keypress or glance away.
- **Consider removing the shared prefix.** If all the rows are under the same directory, show that directory once in a header and list relative paths. That often removes the need to truncate at all.
- **Be consistent.** Use the same strategy for every row so the ellipses line up where users expect them.

Rough sketch (replace `len` with a cell-width function in real code):

```python
def fit_path(path, width):
    if len(path) <= width:
        return path
    *dirs, name = path.split("/")
    if len(name) + 2 > width:  # name alone doesn't fit: cut its middle
        keep = width - 1
        head, tail = keep - keep // 2, keep // 2
        return name[:head] + "…" + name[-tail:]
    out = name
    for d in reversed(dirs):  # add parent dirs while they fit
        cand = d + "/" + out
        if len("…/" + cand) > width:
            break
        out = cand
    return "…/" + out
```

For your example, that gives `…/org.example.Viewer.desktop`, which fits in 30 cells with the full filename intact.
