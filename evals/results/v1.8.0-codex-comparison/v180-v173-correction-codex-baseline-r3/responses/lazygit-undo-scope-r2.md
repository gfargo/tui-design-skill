Lazygit’s default keys are:

- **Undo:** `z`
- **Redo:** `Ctrl+z`

Undo/redo uses Git’s **reflog**, so it can reverse operations such as commits, resets, and rebases.

- **A push:** No. Undo doesn’t reverse changes on the remote. You’d need a revert followed by a push, or a history rewrite and force-push.
- **Discarded working-tree changes:** No. Uncommitted edits aren’t recorded in the reflog, so discard isn’t recoverable through lazygit’s undo.

For your TUI, matching this behavior means treating undo as Git history recovery. Recoverable discards would require separately saving the edits before discarding them.

I couldn’t verify the current upstream documentation because network access failed.