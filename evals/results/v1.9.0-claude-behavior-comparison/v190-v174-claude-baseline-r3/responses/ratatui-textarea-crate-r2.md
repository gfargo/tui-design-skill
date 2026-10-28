I'd use **`tui-textarea`** (rhysd/tui-textarea) for most apps. If you want real modal vim editing built in, use **`edtui`** instead.

### `tui-textarea`: the usual default
- It's the most widely used multi-line editor widget in the Ratatui ecosystem.
- **Emacs-style bindings are built in** (`C-a`, `C-e`, `C-k`, `M-f`, `M-b`, `C-y`, and so on), along with undo/redo, search (regex), selection, yank/paste, line numbers, cursor-line styling and placeholder text.
- **Vim is not built in.** The repo has an `examples/vim.rs` that shows how to build a modal state machine on top of its `CursorMove` / `Scrolling` / `Input` APIs. It works, but you have to write and maintain the vim layer yourself.
- It's easy to embed: `textarea.input(event)` and `frame.render_widget(&textarea, area)`.

### `edtui`: when vim is the main need
- It's a vim-style editor widget for Ratatui with **Normal, Insert and Visual modes, motions and operators** built in.
- It supports optional syntax highlighting through `syntect`, which tui-textarea doesn't have.
- It's heavier and more opinionated, and less flexible if you want non-vim bindings.

### Check Ratatui 0.30 compatibility first
Ratatui 0.30 split the crate up (`ratatui-core`, `ratatui-widgets`, and so on). Widget crates have to depend on a compatible `ratatui` / `ratatui-core` version. If they don't, you get confusing errors like "trait `Widget` is not implemented" caused by two copies of ratatui in your dependency tree. Before you commit to either crate:

```sh
cargo add tui-textarea   # or edtui
cargo tree -d -i ratatui # duplicate ratatui versions = incompatible
```

If the latest crates.io release still targets 0.29, check the repo for an unreleased 0.30 branch, open PRs, or a maintained fork. You can also pin a git dependency until a release ships. I can't confirm the current published state from here, so verify it.

### Summary
| Need | Pick |
|---|---|
| General text input, emacs-ish keys, lightweight | `tui-textarea` |
| Real modal vim editing out of the box | `edtui` |
| Both emacs and vim | `tui-textarea` plus your own vim layer based on its example |

If you share your `Cargo.toml`, I can check the version compatibility for you.
