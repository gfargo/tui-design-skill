Explicitly undo both changes during terminal cleanup; `ratatui::restore()` does **not** reset cursor shape or restore the window title.

- **Cursor:** send `\x1b[0 q` (DECSCUSR reset), or Crossterm’s `SetCursorStyle::DefaultUserShape`. The previous shape cannot be reliably queried. Most terminals restore the user’s configured shape; older xterm uses a blinking block.
- **Title:** before first setting the filename, push the existing title with `\x1b[22;0t`. On exit, pop it with `\x1b[23;0t`. Push once per session, not on every file change.

Run this cleanup alongside Ratatui restoration on normal quit, errors, and panics, and flush the terminal output. Extend the panic cleanup too—Ratatui’s built-in hook only handles its own terminal state.

Title stacks work in xterm, kitty, foot, iTerm2, Alacritty, and tmux. WezTerm, Ghostty, and Windows Terminal ignore them; there, avoid changing the title or offer an explicit fallback such as clearing it, without promising restoration.