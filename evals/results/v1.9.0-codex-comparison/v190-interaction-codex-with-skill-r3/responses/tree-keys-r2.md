Use **arrow keys as the primary controls, with `hjkl` aliases** while the tree has focus. Keep movement, expansion, activation, and marking distinct.

| Key | Recommended behavior |
|---|---|
| `↑` / `k`, `↓` / `j` | Move through visible rows; skip collapsed descendants. |
| `→` / `l` | Expand a branch; if already expanded, move to its first child. Activate a leaf. |
| `←` / `h` | Collapse an expanded branch; otherwise move to its parent. At the root, do nothing. |
| `Enter` | Activate the node. For a purely structural branch, toggle expansion. |
| `Home` / `End` | First / last visible row. Optional `gg` / `G` aliases. |
| `PgUp` / `PgDn` | Move one viewport, retaining one row of overlap. |
| `/` | Filter the tree; retain and expand ancestors of matching nodes. |
| `Space` | Toggle a mark if multi-select exists. Keep marks separate from the focused row. |
| `Tab` / `Shift+Tab` | Move focus between panels. |
| `?` | Show contextual help. |

Printable shortcuts must yield whenever a search or text field owns input.

**Make the tree preserve the user’s place:**

- Store expansion, focus, and marks by **stable node ID**, not row index. Preserve them across refreshes.
- Treat filter-driven expansion as temporary; clearing the filter restores the previous expansion state and position.
- If the focused node disappears, choose its nearest surviving neighbor. If collapsing a branch hides focus, move focus to that branch.
- Load children lazily, without blocking input. Show loading on that branch’s row; distinguish an empty branch from a failed load and offer retry.
- Keep the focused row visible. Mouse-wheel scrolling moves the viewport without silently changing focus.
- If marking branches selects descendants, explicitly define whether that includes hidden or unloaded descendants and show the affected count before bulk actions.

`Esc` cancels the innermost active operation, closes an overlay, or clears filtering/marks; it never quits at the root. `q` backs out of a nested view and quits at the app root. `Ctrl+C` cancels running work first, otherwise quits cleanly.

Assuming a persistent tree with an optional detail pane, use this layout:

```text
Wide                                  60 columns
Files                 Details         Files
- src/                src/main.rs     - src/
  - commands/         Rust source       - commands/
      build.rs                            build.rs
  > main.rs                             > main.rs
+ tests/                              + tests/

/ filter  Enter open  ? help           / filter  Enter open  ? help
```

Here `-` means expanded, `+` collapsed, and `>` marks focus. Use two cells of indentation per level; Unicode disclosure glyphs or connectors can have ASCII fallbacks.

At **80×24**, retain details only if both panes remain useful. At **60 columns**, show the tree alone and open details as a separate view; truncate long names by terminal cell width and expose the full path in details. For very deep trees, shift the visible indentation and show ancestor context. A reasonable initial hard minimum is **40×8**, below which show a resize message with working quit keys.

Keep the visual budget small: **zero nested borders**, one focus cue, and one expansion cue per branch. Remove repeated file icons, leaf bullets, and redundant “folder” labels. Preserve meaning without color, and offer a linear path-based mode when accessibility or automation requires it.