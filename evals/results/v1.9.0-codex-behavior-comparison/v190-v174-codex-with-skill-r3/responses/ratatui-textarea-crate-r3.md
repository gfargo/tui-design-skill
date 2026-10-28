Use **[`ratatui-textarea`](https://github.com/ratatui/ratatui-textarea)**, the Ratatui organization’s maintained fork of `tui-textarea`. It supports **Ratatui 0.30** and provides multi-line editing with Emacs-style shortcuts and customizable input handling for Vim-style bindings.

```sh
cargo add ratatui-textarea
```

For modal Vim behavior, follow its Vim example to manage modes and map keys to editing operations.

Avoid the original `tui-textarea`: it is unmaintained, and its last release, **0.7**, targets **Ratatui 0.29**.