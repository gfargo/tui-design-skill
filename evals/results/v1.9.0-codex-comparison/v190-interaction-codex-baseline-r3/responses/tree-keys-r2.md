A good TUI tree should work with arrow keys alone, with optional Vim-style aliases.

| Key | Behavior |
|---|---|
| `↑` / `↓` | Move to the previous / next visible node |
| `→` / `l` | Expand a collapsed branch; if already expanded, move to its first child |
| `←` / `h` | Collapse an expanded branch; otherwise move to its parent |
| `Enter` | Open or activate the focused node |
| `Space` | Toggle selection, if selection is supported |
| `Home` / `End` | Move to the first / last visible node |
| `PgUp` / `PgDn` | Move roughly one viewport, keeping focus visible |
| Type text | Jump to a matching visible node; clear the prefix after a short pause |
| `/` | Start an explicit search, if supported |
| `Esc` | Cancel search or close a transient mode |
| `?` | Show keyboard help |

If your users expect Vim navigation, add `j` / `k` for down / up. Decide how those keys interact with type-to-jump—unmodified letters cannot reliably do both.

The behaviors matter as much as the bindings:

- **Separate focus from selection.** Moving the cursor should not silently change a multi-selection.
- **Preserve position.** Keep focus and expansion state across refreshes using stable node IDs.
- **Handle collapse predictably.** If a branch containing the focused node collapses, move focus to that branch.
- **Keep navigation local.** Up and down traverse visible rows, without wrapping by default.
- **Show clear states.** Distinguish collapsed, expanded, loading, empty, and failed branches. Leaves should have no expand indicator.
- **Load on demand.** Expanding a branch can fetch children without blocking navigation; provide a retry action on failure.
- **Keep focus visible.** Scroll only as far as needed, and account for indentation when showing long labels.
- **Make destructive actions explicit.** Avoid binding deletion to an easy single-letter key without confirmation or undo.

For a minimal first version, ship arrows, `Enter`, `Home`/`End`, page navigation, and `?`. Add selection, search, and bulk expansion when the task calls for them.