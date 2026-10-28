Use **[`tui-textarea-2`](https://crates.io/crates/tui-textarea-2)**, the maintained fork of `tui-textarea`, for Ratatui 0.30.

It provides multiline editing, selection, undo/redo, and Emacs-style shortcuts. Vim-style modal bindings can be implemented through its input API; check its Vim example rather than expecting full Vim emulation out of the box.

Avoid blindly using the original `tui-textarea`: releases targeting older Ratatui versions can cause incompatible widget types.

I couldn’t verify the live release metadata here, so check the selected version’s Ratatui dependency before pinning it.