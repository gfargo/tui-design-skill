**Keys:** `z` is undo and `Z` (Shift+z) is redo. Both work from any panel.

**How it works:** lazygit doesn't keep its own action history. It reads the **git reflog**, finds the last HEAD movement it can undo (a commit, reset, rebase, checkout, amend and so on), and runs the matching `git reset` or `git checkout` to go back to the previous state. Redo walks forward again. It writes markers in the reflog so it can tell its own undo/redo steps apart from your actions. Before it changes anything, it shows a confirmation saying what it's about to do.

**Can it undo a push?** No. A push changes the remote, and the reflog only records your local HEAD. Undoing the commit afterwards only moves your local branch. You'd need a force-push to change the remote, and lazygit won't do that as part of undo.

**Can it undo a discarded working-tree change?** No. Changes that were never committed aren't in the reflog, so once you discard them, git has no copy to restore. The same goes for staging/unstaging and stash operations. Creating or deleting branches isn't in HEAD's reflog either, so undo doesn't cover those. If you undo while you have uncommitted changes, lazygit offers to auto-stash them so they aren't lost during the reset.

**If you're building this yourself**, the main choice is whether to copy that design:

- **Reflog-based (lazygit's way):** It's stateless, survives restarts, and also covers commits made outside your TUI. It inherits the same limits: no remote operations and nothing that wasn't committed.
- **To make discards undoable** (which lazygit can't do), save the content before deleting it. For example, run `git stash create` or write the blob with `git hash-object -w`, and keep the hash in your own undo stack. That one change would make your undo safer than lazygit's.
- **For pushes**, the honest option is not to make them undoable, and to show "can't undo" in the confirmation step. Undoing a push really means force-pushing to a shared remote.

This is from memory of lazygit's docs ("Undoing" in the lazygit repo docs), not from checking a current release. The `z`/`Z` keys have been stable for years, but check the docs if you need exact edge-case behaviour.
