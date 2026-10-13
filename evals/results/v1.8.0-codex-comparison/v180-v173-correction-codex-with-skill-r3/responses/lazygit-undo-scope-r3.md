Lazygit’s default keys are **`z` for undo** and **`Z` (Shift+z) for redo**.

Its undo uses Git’s **reflog**, so it can undo commits, checkouts, resets, and even a completed rebase. It is unavailable during an ongoing rebase.

- **Undo a push? No.** Undo does not reverse changes on the remote.
- **Recover a discarded working-tree change? No.** Reflog-based undo does not restore discarded uncommitted edits.

For your TUI, copy those bindings and clearly state the limits. Confirm before discarding changes; if you want discard to be undoable, save the affected content separately before deleting it.