Lazygit’s default bindings are **`z` to undo** and **`Z` (Shift+z) to redo**.

Its undo uses Git’s **reflog**, so it can reverse commits, checkouts, resets, and even a completed rebase. It is unavailable during an ongoing rebase.

It **cannot undo a push or restore a discarded working-tree change**. Stash changes and branch creation are also outside its undo support.

For your TUI, use the same keys, make the undo limits visible, and require confirmation before discarding changes unless you save a recoverable snapshot first.