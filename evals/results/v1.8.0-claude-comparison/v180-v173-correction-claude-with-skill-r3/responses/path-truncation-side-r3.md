**No. Don't cut the end of a path.** With tail truncation the filename is the part that disappears, and that's the part people scan for. In a 30-cell column, your example becomes:

```
/usr/local/share/applications…
```

Every other file in that directory would look exactly the same.

**Truncate from the start instead**, and cut at a `/` so the visible piece is a whole path segment:

```
…/org.example.Viewer.desktop      (28 cells)
```

**Middle truncation** keeps the root as well (`/usr/…/org.example.Viewer.desktop`). Use it when the root tells entries apart, for example `/usr` versus `/home`. Your example needs 33 cells that way, so it doesn't fit in 30. A reasonable rule is to try middle truncation first and fall back to start truncation when it doesn't fit.

Some details to handle:

- **Long filenames.** If the filename alone is wider than the column, shorten it in the middle and keep the extension, e.g. `org.example.Very…ewer.desktop`. Never show just `…`.
- **Leave room for the ellipsis.** `…` takes 1 cell and the ASCII fallback `...` takes 3. Count terminal cells, not `len()`, or CJK and emoji names will break your alignment. `…` is also an East Asian "ambiguous-width" character, so it can render 2 cells wide in some terminals and locales. Keep the `...` fallback easy to switch to.
- **Show the full path somewhere.** Put the selected row's full path in a status line or detail pane, and open details on Enter. Truncating is fine as long as the user is one keypress away from the whole value.
- **Don't wrap.** Wrapped rows in a list break the row rhythm and make the cursor jump.

Also check whether the list needs to repeat the directory on every row. If most entries share a parent, show the directory once in the pane title, list only basenames, and the overflow mostly goes away. This is the same idea as yazi's and ranger's Miller columns. The directory prefix repeated on every row is chrome, not data.

This follows the skill's truncation guidance in `references/visual-patterns.md:458-467`: start or middle truncation for paths, tail truncation for prose and IDs.
