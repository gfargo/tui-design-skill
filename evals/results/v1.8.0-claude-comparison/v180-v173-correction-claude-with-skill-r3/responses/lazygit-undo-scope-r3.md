In lazygit, **`z` is undo and `Z` (Shift+z) is redo.** It can't undo a push or a discarded working-tree change.

**How it works:** lazygit's undo reads the **git reflog**. It can walk back anything recorded there: commits, checkouts, resets, and even a whole botched rebase. It moves back through reflog entries rather than keeping its own history of actions.

**What it can't undo:**
- **Pushes.** The remote has already changed, and the local reflog can't change it back.
- **Discarded working-tree changes.** Uncommitted edits never reach the reflog, so once they're discarded nothing records them.
- **Stash changes.**
- **Branch creation.**
- **Anything while a rebase is in progress.** Undo is turned off until the rebase finishes or is aborted.

**What to copy for your TUI:**
1. **Use `z`/`Z`** if you want lazygit users to feel at home. Show them in the footer or help screen so people can find them.
2. **Use the reflog for history** rather than building your own action stack. Git already records the reversible operations.
3. **Be clear about the limits.** When someone presses `z` and the last action can't be undone (a push, a discard), say so in the status line. Don't do nothing silently or undo some older action instead.
4. **Ask for confirmation before anything that can't be undone.** Discarding changes and pushing (especially force-pushing) should show a confirmation dialog, because neither can be reversed. The rule is: either confirm or offer undo, and never destroy work silently.
5. **Optional, beyond lazygit:** you could make discards undoable by snapshotting first, for example with `git stash create` or by writing the blob to a temp ref before discarding. This is the "state snapshot" approach: it costs a bit of storage, but it covers the case people regret most.

Sources: `references/interaction-patterns.md` → *Undo / redo*, and `references/exemplar-apps.md` → lazygit.
