**Short answer:** use **`tui-textarea`** if you want both emacs and vim bindings. Use **`edtui`** if vim-style modal editing is the main goal.

### `tui-textarea` (rhysd/tui-textarea)
- The most widely used multi-line editor widget in the Ratatui ecosystem.
- **Emacs-style keybindings are built in** (`Ctrl-A/E/F/B/N/P/K/Y`, `Alt-F/B`, etc.).
- **Vim bindings are not built in.** The repo ships a `vim` example with a small modal state machine (Normal/Insert/Visual/Operator-pending) that you copy into your app. It works well for basic motions, operators, and yank/paste.
- Also has undo/redo, search (regex), line numbers, selection, a placeholder, a masked (password) mode, and custom styling.
- You feed it events with `textarea.input(event)`, or `input_without_shortcuts` if you want to handle every key yourself. That makes it easy to put your own keymap layer on top.

### `edtui`
- Built around a vim-style modal editor: Normal/Insert/Visual modes, motions, a register-like clipboard, and optional syntax highlighting (via `syntect`).
- A better fit if you want something close to a mini-vim with little glue code. It's less suited to emacs-style editing.

### Ratatui 0.30 compatibility
Ratatui 0.30 split into `ratatui-core` and `ratatui-widgets`. Widget crates pinned to 0.29 will pull in a second copy of ratatui, and their `Widget` impls won't match your types. Before you commit to a crate:

1. Check the crate's `Cargo.toml` or crates.io page for `ratatui = "0.30"` (or a `ratatui-core` dependency).
2. After adding it, run `cargo tree -d -i ratatui` and make sure only one version shows up.
3. If the latest `tui-textarea` release still targets 0.29, look for a newer release, the repo's `main` branch (`git = "..."`), or a maintained fork. A git dependency is a fine short-term option.

### Recommendation
- **You need both emacs and vim bindings, or a general-purpose input box:** `tui-textarea`, with its vim example adapted into your app.
- **The editor is a core, vim-centric feature:** `edtui`.

I'm not certain which exact versions of each crate support Ratatui 0.30 right now, so check that before you pick. If you want, I can look at your `Cargo.toml` and check compatibility.
