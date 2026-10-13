Explicitly undo the cursor shape and title changes alongside Ratatui’s normal cleanup. `ratatui::restore()` doesn’t restore these app-managed settings.

- **Cursor:** send `CSI 0 SP q` (`"\x1b[0 q"`) to reset its shape, and ensure it’s visible. The previous shape can’t be reliably queried. Most terminals restore the configured default; older xterm uses a blinking block.
- **Title:** before setting the first filename title, push the original with `CSI 22 ; 0 t` (`"\x1b[22;0t"`). On exit, pop it with `CSI 23 ; 0 t` (`"\x1b[23;0t"`). Push once per session, not on every file change.

Title restoration is best-effort: WezTerm, Ghostty, and Windows Terminal ignore the title stack. Offer an option to disable title changes there; clearing the title doesn’t recover the original.

Run this cleanup on normal quit, errors, and panics, and before temporary terminal handoffs such as suspend. Flush the terminal output, and verify quitting directly from insert mode as well as error and panic paths.