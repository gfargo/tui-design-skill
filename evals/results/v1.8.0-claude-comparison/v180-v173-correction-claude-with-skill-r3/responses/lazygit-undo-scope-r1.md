Lazygit uses **`z` for undo and `Z` (Shift+z) for redo**.

**Short answer: no to both.** Lazygit can't undo a push or a discarded working-tree change.

Its undo is built on the **git reflog**, so it can only reverse things the reflog records:

- **Can undo:** commits, checkouts, resets, and even a whole botched rebase.
- **Can't undo:**
  - **Pushes.** The remote has already changed, and the reflog only tracks your local refs.
  - **Working-tree changes**, including discards. Uncommitted changes were never stored as objects, so there's nothing to restore.
  - **Stash changes.**
  - **Branch creation.**
- **Not available mid-rebase.** Undo is disabled while a rebase is in progress.

**What to copy for your git TUI:**

1. **Use the same keys and the same reflog-based model.** Users coming from lazygit will expect `z`/`Z`.
2. **Tell users about the limits.** If someone presses `z` and the last action can't be undone, say so in the status line (e.g. "Can't undo: push already sent to the remote") instead of silently skipping it.
3. **Confirm anything you can't undo.** Discarding changes, pushing (especially force-push) and dropping a stash need a confirmation dialog, because undo won't save the user. The general rule is: if a single key can destroy something, either confirm it or make it undoable.
4. **Optionally go further than lazygit on discards.** Before discarding, you could save the changes somewhere first (e.g. `git stash create` plus storing the SHA, or writing the blobs with `git hash-object -w`). Then a discard could be undone too. That's an improvement on lazygit, not something lazygit does.

Sources: the skill's `references/interaction-patterns.md:363-372` (Undo / redo) and `references/exemplar-apps.md:47` (lazygit case study).
