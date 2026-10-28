Use **[`ratatui-textarea`](https://crates.io/crates/ratatui-textarea)**, the maintained successor to `tui-textarea`, for a Ratatui 0.30 app.

It provides multiline editing, selection, undo/redo, and Emacs-style shortcuts. Vim-style modal editing requires a small input-handling layer; see the crate’s Vim example.

Avoid blindly using older `tui-textarea` releases: their Ratatui dependency can cause incompatible widget types with 0.30. I couldn’t verify the latest release metadata here, so check the selected version’s compatibility before pinning it.