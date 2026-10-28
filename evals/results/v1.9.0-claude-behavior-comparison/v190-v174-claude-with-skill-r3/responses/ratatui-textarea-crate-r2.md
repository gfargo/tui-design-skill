Use **`ratatui-textarea`**.

- **It's the maintained version.** It's the Ratatui org's fork of `tui-textarea` and supports Ratatui 0.30.
- **Don't use `tui-textarea`.** It's no longer maintained, and its last release (0.7) only works with Ratatui 0.29. Using it with 0.30 means two Ratatui versions in one build.
- **Install it from crates.io or `github.com/ratatui/ratatui-textarea`.** A malicious GitHub fork with the same name was taken down in March 2026, so don't install from a GitHub fork you haven't checked.

```toml
[dependencies]
ratatui = "0.30"
ratatui-textarea = "*"  # pin to the current release from crates.io
```

About the bindings (this part comes from my general knowledge of the `tui-textarea` lineage, not the skill's reference): the built-in keymap is emacs-style (Ctrl+F/B/N/P/A/E, and so on). Vim-style modal editing isn't built in. You add it with a small mode state machine that maps keys to the textarea's cursor and edit calls, and the repo has an example to start from. If you want full vim behaviour (modes, motions, registers) without writing it yourself, look at `edtui`. Check that its current release supports Ratatui 0.30 before you adopt it.
