In lazygit, **`z` is undo and `Z` is redo.** It **can't undo a push or a discarded working-tree change.**

**How it works:** lazygit's undo reads the git reflog. It can reverse anything the reflog records, such as commits, checkouts, resets and even a whole botched rebase. Anything outside the reflog can't be undone:

- **Pushes:** the remote has already changed, and the local reflog can't reverse that.
- **Discarded working-tree changes:** those edits were never committed, so the reflog has nothing to restore.
- **Stash changes** and **branch creation** are also out of scope.
- Undo is also **turned off while a rebase is in progress**.

**What to copy for your TUI:**

1. **Base undo on the reflog for git history.** You get commits, resets, checkouts and rebases almost for free, and redo is just moving forward again through the same entries.
2. **Ask for confirmation before anything undo can't reverse.** Discarding changes and force-pushing should open a confirmation dialog. The rule is: an action either has undo or asks first, and nothing is ever destroyed silently.
3. **Be clear about the limits.** If someone presses `z` mid-rebase, or after an action undo can't reverse, show a short message saying why instead of doing nothing.
4. **Optional, and my own idea rather than something lazygit does:** before discarding, save the changes as a dangling stash object (`git stash create` plus a saved ref). That would make discards recoverable and go one step beyond lazygit.

Sources: the skill's `references/interaction-patterns.md:363-372` (Undo / redo) and `references/exemplar-apps.md:47` (lazygit case study).
