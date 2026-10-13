On exit, restore the cursor style to the terminal’s default and restore the previous window title.

With Crossterm, use `SetCursorStyle::DefaultUserShape` and bracket your title change with `PushTitle` / `PopTitle` where supported. Don’t hard-code a block cursor or an empty title; users may have their own defaults.

Include these in your terminal cleanup alongside showing the cursor, leaving the alternate screen, and disabling raw mode. Run cleanup on normal exits, errors, and panics.