Explicitly undo both changes on every exit path—normal quit, errors, and panics. Ratatui’s `restore()` handles standard terminal teardown but does **not** reset cursor shape or restore your title.

- **Cursor:** emit `\x1b[0 q` (DECSCUSR reset). This requests the terminal default; some terminals restore the user’s configured shape, while older xterm uses a blinking block. The previous shape cannot be reliably queried and saved.
- **Title:** before setting the first file title, push the existing title with `\x1b[22;0t`. On exit, pop it with `\x1b[23;0t`. Push once per session, not on every file change.

Title restoration depends on terminal support: WezTerm, Ghostty, and Windows Terminal ignore the title stack. For those, offer an option to disable title changes or use an explicit fallback; clearing the title does not restore the original.

Keep Ratatui’s managed lifecycle, add your custom cleanup before panic reporting, and attempt each cleanup step independently so one failure does not prevent the rest. Verify quitting from insert mode, returned errors, and panics in a real terminal.