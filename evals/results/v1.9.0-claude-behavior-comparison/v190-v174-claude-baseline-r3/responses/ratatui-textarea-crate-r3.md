**Recommendation: [`tui-textarea`](https://github.com/rhysd/tui-textarea)**, with one caveat about Ratatui 0.30 that I explain below.

### Why `tui-textarea`
- **Emacs-style bindings by default:** `Ctrl+F/B/N/P`, `Ctrl+A/E`, `Ctrl+K` (kill), `Ctrl+Y` (yank), `Alt+F/B` and so on, through `textarea.input(key)`.
- **Vim-style editing:** it doesn't include a modal vim mode. Instead you get a cursor and editing API (`CursorMove`, `delete_word`, `start_selection`, `undo`, etc.), and the repo has an `examples/vim.rs` showing a normal/insert/visual state machine built on it. Copy that and adapt it.
- **Also included:** undo/redo, selection with copy/paste, search (with the `search` feature, which uses regex), line numbers, placeholder text, masking (for password fields), and per-line styles.
- It's the most widely used option and is easy to embed. It renders like any other widget: `frame.render_widget(&textarea, area)`.

### The Ratatui 0.30 caveat
`tui-textarea` depends on `ratatui` directly. If its released version targets an older Ratatui (0.7.x targets 0.29), you end up with two copies of Ratatui. Rendering then fails with a confusing error like "`Widget` is not implemented for `&TextArea`". Before you commit:

```sh
cargo add tui-textarea
cargo tree -d -i ratatui   # if two ratatui versions show up, it won't work
```

If they don't match, look for a newer release or a git branch that supports 0.30, or a maintained fork. Ratatui 0.30's `ratatui-core` split was meant to make widget crates less tightly tied to a Ratatui version, but each crate has to adopt it.

### Alternative: [`edtui`](https://github.com/preiter93/edtui)
Choose this if vim is your main need. It has **built-in modal vim editing** (normal/insert/visual modes, motions, registers) and optional syntax highlighting, so you don't build the state machine yourself. It's more opinionated and less flexible as a plain input box. I believe newer versions added emacs-style bindings too, but check its README before relying on that. The same Ratatui version check applies.

### Quick guide
| Need | Pick |
|---|---|
| Emacs bindings, full control, vim if you're willing to wire it up | `tui-textarea` |
| Vim modal editing out of the box, code-editor feel | `edtui` |

My knowledge of which versions support 0.30 may be out of date, so `cargo tree -d` is the reliable check.
