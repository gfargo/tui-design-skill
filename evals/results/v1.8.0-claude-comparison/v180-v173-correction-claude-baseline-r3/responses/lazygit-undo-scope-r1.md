In lazygit, **`z` is undo and `Ctrl+Z` (`<c-z>`) is redo**. You can rebind them with `keybinding.universal.undo` and `keybinding.universal.redo` in `config.yml`.

**It can't undo either of the things you asked about.** Lazygit's undo is built on the **git reflog**. Undo walks back through reflog entries and moves you to the earlier state: checkouts, commits, resets, rebases, amends and similar actions that move `HEAD` or a branch. Anything that doesn't leave a reflog entry is out of reach:

- **Push:** no. Undo only changes your local refs, so the remote keeps what you pushed. To reverse a push you'd have to undo locally and then force-push yourself.
- **Discarded working-tree changes:** no. Uncommitted changes aren't in the reflog, so once lazygit discards them they're gone (unless your editor or OS kept a copy).
- **Also not covered:** staging and unstaging, stash operations, and other changes outside refs, such as remotes and config.

**Two behaviours worth copying:**
- Before undoing or redoing, lazygit shows a confirmation that names the action it's about to reverse, like "undo checkout to branch X". It doesn't just do it silently.
- Undo and redo run on a `git reset`/checkout, so lazygit can refuse to run or ask you to confirm when you have uncommitted changes that could be lost.

**For your TUI:** reflog-based undo is cheap and robust because git already keeps the history. If you want to go beyond lazygit, the most useful extra is protecting discards. Snapshot the changes first, for example with `git stash create` plus storing the SHA, or by writing the blobs with `git hash-object -w`, so a discard can be undone. Make it clear in the UI that pushes are never undoable.

I answered from memory of lazygit's docs (`docs/Undoing.md` and `docs/Config.md` in the lazygit repo) and didn't look anything up here. Check those files if you need exact wording or recent changes.
