Use **`ratatui-textarea`**.

- It's the Ratatui org's maintained fork of `tui-textarea`. It provides a multi-line editor widget with vim/emacs-style bindings and supports Ratatui 0.30.
- **Avoid `tui-textarea`.** It's unmaintained, and its last release (0.7) requires Ratatui 0.29, so it won't work with 0.30.
- **Install it from crates.io** (`cargo add ratatui-textarea`) or from the official repo at `github.com/ratatui/ratatui-textarea`. Don't use a random GitHub fork: a malicious fork with the same name was taken down in March 2026.

If you only need a single-line input, `tui-input` is the lighter option.

This comes from the skill's Rust ecosystem reference (`references/ecosystem-rust.md:274`). I didn't check crates.io for the current version, so look at the latest release before you pin one.
