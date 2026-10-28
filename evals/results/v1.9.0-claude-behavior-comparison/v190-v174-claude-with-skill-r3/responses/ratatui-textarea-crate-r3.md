Use **`ratatui-textarea`**.

- **It works with Ratatui 0.30.** It's the Ratatui org's maintained fork of `tui-textarea` and gives you a multi-line editor with vim/emacs-style bindings.
- **Skip `tui-textarea`.** Most older tutorials use it, but it's unmaintained. Its last release (0.7) requires Ratatui 0.29, so it won't build cleanly against 0.30.
- **Install from crates.io or the official repo.** That repo is `github.com/ratatui/ratatui-textarea`. A malicious GitHub fork with the same name was taken down in March 2026, so don't add it as a git dependency from any other GitHub account.

```toml
[dependencies]
ratatui = "0.30"
ratatui-textarea = "*"   # pin to the current crates.io release
```

If you also need a single-line field, like a search box or prompt, `tui-input` is the lighter option for that.

This comes from the tui-design skill's Rust reference (`references/ecosystem-rust.md:274`). I didn't check crates.io for the latest version number, so run `cargo add ratatui-textarea` to get the current one.
