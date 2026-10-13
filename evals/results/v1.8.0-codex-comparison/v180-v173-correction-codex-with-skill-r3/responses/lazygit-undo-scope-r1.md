Lazygit’s default bindings are **`z` for undo** and **`Z` (Shift+z) for redo**.

Its undo uses Git’s **reflog**, covering actions such as commits, checkouts, resets, and completed rebases.

- **Undo a push? No.** Undo doesn’t reverse changes on the remote.
- **Undo a discarded working-tree change? No.** The reflog doesn’t preserve uncommitted file contents.

For your TUI, use those keys and make the limits explicit. Confirm discards unless you save a recoverable snapshot first.