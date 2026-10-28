I didn't find any source files in this directory, so this is general advice rather than a code change. If you share the file, I can make the edits.

The row feels busy because it uses three markers that all mean the same thing, and the double boxing doubles the visual weight around it.

## 1. Use one status marker per row

`[PASS]` and `(ok)` both say the test passed. Keep a single glyph and let color carry the rest:

```
> ✓ build        2.1s
  ✓ lint         0.8s
  ✗ unit-tests   4.3s
  ● e2e          …
```

- **Glyph and color:** green `✓` for pass, red `✗` for fail, yellow or spinning `●` for running, dim `○` for pending. The shape still works on terminals without color, and color makes the list easy to scan.
- **No brackets:** `[ ]` and `( )` add characters without adding meaning.
- **Name is the main content:** show it in the default foreground. The name is what people read.
- **Duration is secondary:** right-align it so the numbers line up, and dim it.

## 2. Show the selection one way

Use either the `>` cursor or a highlighted row, not both. Reverse video or a subtle background on the selected row usually looks cleaner, and it frees up the left column. If you keep `>`, make it the only thing in that column.

## 3. Remove a box

Nested borders spend 4 columns and 4 rows on decoration and make the content feel boxed in. Options, from cleanest to least clean:

- **No border.** Use a bold or dim title line and whitespace instead:
  ```
  Tests  3/4 passed

  > ✓ build        2.1s
    ✓ lint         0.8s
  ```
- **One border** with the title embedded in it:
  ```
  ╭─ Tests 3/4 ──────────────╮
  │ ✓ build             2.1s │
  ╰──────────────────────────╯
  ```
- If the outer box exists to separate panes, keep that box and drop the inner one. A single divider line between panes often does the same job.

## 4. Optional: put a summary at the top

A single header like `3 passed · 1 failed · 4.2s` means the rows don't need to tell the whole story.

Tell me which framework you're using (Bubble Tea/Lip Gloss, Ink, Textual, Ratatui, etc.) and I can show the specific styling calls, such as Lip Gloss's `Faint(true)` or Ink's `dimColor`.
