Lazygit’s default keys are:

- **Undo:** `z`
- **Redo:** `Ctrl+z`

Its undo/redo relies on Git’s **reflog**, so it can undo local history changes such as commits, resets, merges, and rebases.

It **cannot undo a push** on the remote, or **restore discarded, uncommitted working-tree changes**. Matching that behavior in your TUI means treating undo as local history recovery; recovering discarded edits would require your own snapshots or backups.