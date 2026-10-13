Lazygit’s default keys are:

- **`z` — undo**
- **`Ctrl+z` — redo**

Undo/redo uses Git’s **reflog** to recover previous local history states, such as before a commit, reset, or rebase. It isn’t a general undo stack for every action.

- **Push:** Undo doesn’t reverse changes on the remote. You’d need to revert the pushed commits and push again, or reset locally and force-push.
- **Discarded working-tree change:** Undo can’t restore discarded uncommitted edits; the reflog doesn’t record working-tree contents.

For your TUI, matching lazygit means history-based undo/redo. Recovering discarded edits would require your own snapshots or backups.

[Keybindings](https://github.com/jesseduffield/lazygit/blob/master/docs/Keybindings_en.md) · [Undo/redo documentation](https://github.com/jesseduffield/lazygit/blob/master/docs/Undoing.md)

I couldn’t retrieve the live docs in this session, so I couldn’t verify recent changes.