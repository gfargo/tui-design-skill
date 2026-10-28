Use **arrows with optional `hjkl` aliases**, and keep navigation, expansion, and activation predictable. Assuming the tree is a panel in a full-screen TUI, I’d use this keymap:

| Key | Behavior |
|---|---|
| `↑` / `k`, `↓` / `j` | Move through visible rows; skip collapsed descendants. |
| `→` / `l` | Expand a closed branch; enter its first child when open; activate a leaf. |
| `←` / `h` | Collapse an open branch; otherwise move to its parent. At the root, stay put. |
| `Enter` | Toggle a branch; activate a leaf. If branches have a primary action, use Enter for that and arrows for expansion. |
| `Home` / `End` | First / last visible row. Optional `gg` / `G` aliases. |
| `PgUp` / `PgDn` | Move one viewport, retaining one row of overlap. |
| `/` | Filter by name or path. |
| `Space` | Toggle a mark if multi-select exists. |
| `Tab` / `Shift+Tab` | Move focus between panels. |
| `?` | Show contextual help. |

Printable shortcuts apply only when a text field doesn’t own input.

The behaviors matter as much as the bindings:

- **Preserve position.** Store expansion and cursor state by stable node ID. Refreshing shouldn’t reset the tree or scroll it unexpectedly. If the current node disappears, prefer its surviving parent, then a nearby row.
- **Filter with context.** Keep matching nodes and their ancestors visible, temporarily expanding those paths. Clearing the filter restores prior expansion state; cancelling restores the prior cursor position.
- **Load locally.** Fetch children lazily without blocking input. Show loading on the expanding branch. Distinguish an empty branch from a failed load, and offer retry on failure.
- **Separate cursor and marks.** Collapsing a branch can preserve hidden marks, but show the total marked count and make batch-action scope explicit. Default Space to marking that node only; recursive marking should be a separate action.
- **Keep navigation safe.** Moving the cursor may update a preview; it shouldn’t execute the item’s primary action.
- **Use the quit ladder.** Esc cancels work, closes an overlay, clears filtering or marks, then backs out—one applicable step per press. Esc never quits. `q` goes back or quits at the app root; Ctrl+C cancels work first, otherwise quits cleanly.

For presentation, use two cells of indentation per level, branch disclosure markers, and one clear cursor highlight. Provide ASCII equivalents and preserve meaning without color.

```text
Wide: tree + preview                    60-column split: tree only
Files                 Preview           Files
v src/                main.go           v src/
  > internal/         package main        > internal/
    main.go                             >   main.go
> tests/                                > tests/

/ filter  Enter open  Space mark  ?      / filter  Enter open  ?
```

Here `v` means expanded, `>` means collapsed, and the extra `>` in the narrow sketch marks the cursor; in practice, reverse video avoids that ambiguity.

At **80×24**, retain a preview only if both panes remain useful. At **60 columns**, give the tree the full width and open details on demand. Truncate long labels by terminal-cell width and reveal the full path in details; for extreme depth, offer a subtree drill-down with breadcrumbs. Below the declared usable minimum, show the required dimensions while keeping exit keys working.

Clutter budget: **zero nested borders**, one cursor cue, and disclosure markers only on branches. Remove repeated file icons or metadata that don’t help the browsing task; keep the footer to 3–5 contextual hints.