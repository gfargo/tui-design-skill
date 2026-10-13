On exit, restore the terminal’s cursor style to its default and restore the previous window title. Showing the cursor alone won’t reset its shape.

With Crossterm, use `SetCursorStyle::DefaultUserShape` and pair `PushTitle` at startup with `PopTitle` during cleanup where supported. Also disable raw mode, leave the alternate screen, and show the cursor.

Run cleanup on normal exit, errors, and panics so terminal state is restored consistently.