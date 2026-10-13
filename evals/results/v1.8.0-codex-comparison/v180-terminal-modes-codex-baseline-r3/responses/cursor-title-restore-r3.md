On exit, restore the terminal state your editor changed:

- Reset the cursor to the terminal’s default shape (`SetCursorStyle::DefaultUserShape` in Crossterm).
- Restore the previous window title if you saved it or used terminal title push/pop support. Otherwise, clear the title or set a neutral fallback; the original title generally can’t be queried portably.
- Disable raw mode, leave the alternate screen, and show the cursor.

Run this cleanup on normal exit, error paths, and panics. Ratatui’s terminal restoration alone may not undo custom cursor styles or window titles.