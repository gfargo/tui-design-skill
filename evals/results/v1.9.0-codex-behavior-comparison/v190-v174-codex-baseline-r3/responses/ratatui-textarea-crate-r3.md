Use **[`ratatui-textarea`](https://crates.io/crates/ratatui-textarea)**, the maintained fork of `tui-textarea`, choosing a release compatible with Ratatui **0.30**.

It provides a multiline `TextArea` with undo/redo, selection, search, and Emacs-style shortcuts. Vim-style modal bindings require an application-side key handler; its Vim example is a useful starting point.

Avoid blindly using the original `tui-textarea`: releases targeting older Ratatui versions can cause incompatible widget types.

I couldn’t verify the current release metadata, so check the crate’s Ratatui dependency before pinning a version.