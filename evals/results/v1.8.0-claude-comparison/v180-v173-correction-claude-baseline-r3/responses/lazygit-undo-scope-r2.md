**Keys (lazygit defaults):**
- **Undo:** `z`
- **Redo:** `Ctrl+Z` (`<c-z>`), not `Shift+Z`

You can change both in the config under `keybinding.universal.undo` / `redo`.

**How it works:** lazygit's undo is built on the **reflog**. When you press `z`, it reads the reflog to find what the last action did, then works out the git command that reverses it. That's usually a `git checkout` back to the previous branch, or a `git reset` to the previous HEAD. It shows you that command and asks you to confirm before running it. Redo moves forward through the same reflog history. The upside is that undo still works for actions you ran outside lazygit, and it survives restarts, because there's no separate undo stack to keep.

**Your two questions:**

1. **Push: no.** A push changes the remote, not your local reflog, so lazygit can't reverse it. The same goes for anything else that touches a remote, like fetch or pull on the remote side. If you undo a commit that you've already pushed, only your local branch moves. You'd then need a force-push to update the remote, and lazygit won't do that as part of undo.

2. **Discarded working-tree changes: no.** Uncommitted changes that you discard never reach the reflog, or any git object, so lazygit has nothing to restore them from. Stash operations and changes to the index aren't covered either. lazygit's docs list these as limits of reflog-based undo.

**What it can undo:** anything that moves HEAD or a branch ref and gets logged in the reflog. That covers commits, amends, resets, rebases (including interactive ones), merges, cherry-picks and checkouts or branch switches.

**If you're copying this for your TUI:**
- Base undo on the reflog, not on an in-app history. You get persistence and outside-tool actions for free, and your undo will behave the way lazygit users expect.
- Show the reversing command and ask for confirmation, as lazygit does. Undo runs `reset`/`checkout`, which can be destructive.
- Handle a dirty working tree before you reset, for example by refusing or by auto-stashing.
- If you want to beat lazygit on discards, snapshot the changes before a discard. You could run `git stash create` and save the SHA in a ref of your own, or write the changed blobs with `git hash-object -w`. Undo of a discard then becomes possible. That's an addition lazygit doesn't have, so make it clear to users.
