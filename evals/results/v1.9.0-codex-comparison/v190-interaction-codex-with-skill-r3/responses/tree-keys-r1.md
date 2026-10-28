Use **arrow keys as the primary controls, with `hjkl` aliases** when no text field owns input. Assuming a tree panel in a full-screen TUI, I’d use this default:

| Key | Behavior |
|---|---|
| `↑` / `k`, `↓` / `j` | Move through visible rows; skip collapsed descendants. |
| `→` / `l` | Expand a closed branch; enter its first child if already expanded; activate a leaf. |
| `←` / `h` | Collapse an expanded branch; otherwise move to its parent. At the root, do nothing. |
| `Enter` | Activate the node. For branches without another action, toggle expansion. |
| `Home` / `End` | First / last visible row. Optional `gg` / `G` aliases. |
| `PgUp` / `PgDn` | Move one page, keeping one row of overlap. |
| `/` | Filter the tree. |
| `Space` | Toggle a mark, if multi-select is supported. |
| `Tab` / `Shift+Tab` | Move focus between panels. |
| `?` | Show contextual help. |

**Keep navigation, expansion, and marking separate.** Moving the cursor should never activate an item. If branches also have an action, make `Enter` perform it and reserve left/right for expansion.

The behaviors that matter most:

- **Preserve context.** Track focus and expansion by stable node ID across refreshes. If a node disappears, prefer its surviving parent or a nearby row.
- **Filter with ancestry.** Keep matching nodes’ ancestors visible and temporarily expanded. Clearing the filter restores the previous expansion and position. Distinguish “no matches” from an empty tree.
- **Load locally.** Fetch children lazily without blocking input. Show loading or failure beside the affected branch, with retry available. An empty branch must stop looking expandable.
- **Collapse predictably.** If a branch containing the focused descendant collapses, move focus to that branch.
- **Define marking scope.** Default to marking only the current node. Recursive descendant selection should be an explicit, named action; show the marked count, including hidden marks.
- **Respect text entry.** While filtering, printable keys—including `h`, `j`, `q`, and Space—type text.
- **Use the exit ladder.** `Esc` cancels loading, closes an overlay, clears filtering/marks, or backs out—one applicable step per press; it never quits. `q` backs out or quits at the app root. `Ctrl+C` cancels work first, otherwise quits cleanly.

Use two cells of indentation per level, a disclosure marker for branches, and a visible focus cue that survives monochrome. Show the focused node’s full path separately so deep nesting and truncation don’t hide its identity.

```text
Wide: tree + detail                  60 columns: tree only
Files             | Details          Files
  - src           | src/main.rs        - src
    > main.rs     | ...                  > main.rs
  + tests         |                    + tests
Enter open  / filter  ? help          Enter open  / filter  ? help
```

At **80×24**, retain details only if both panes remain useful; at **60 columns**, use one tree pane and open details as a drill-down. Truncate labels by terminal cell width, preserve the selected label over excessive indentation, and declare a minimum such as **40×8**, below which you show a resize message with quit controls.

For clutter, this design needs **zero nested borders**, one focus marker, and one expansion marker per branch. Skip repeated file icons, leaf bullets, and decorative connector lines unless they materially help users follow the hierarchy. Keep one footer line with the current actions and `?`.