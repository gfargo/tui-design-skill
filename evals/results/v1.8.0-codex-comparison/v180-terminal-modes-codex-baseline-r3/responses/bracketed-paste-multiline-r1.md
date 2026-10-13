This is usually **paste being interpreted as typing**. Without bracketed paste enabled, the terminal sends pasted text as ordinary input; each newline becomes an Enter key event, and your Enter handler submits each line.

The fix belongs in terminal setup and event handling, not the Ratatui widget. With Crossterm:

```rust
use crossterm::{
    event::{
        DisableBracketedPaste, EnableBracketedPaste,
        Event, KeyCode, KeyEventKind,
    },
    execute,
};

// During terminal setup:
execute!(std::io::stdout(), EnableBracketedPaste)?;

// In your event loop:
match event {
    Event::Paste(text) => {
        // Single-line policy: reject multiline pastes.
        // Alternatively, open a multiline editor preserving the text.
        if text.contains('\n') || text.contains('\r') {
            app.show_error("Multiline paste rejected; paste a single command.");
        } else {
            app.insert_text(&text);
        }
        // Never submit from this branch.
    }
    Event::Key(key)
        if key.kind == KeyEventKind::Press
            && key.code == KeyCode::Enter =>
    {
        app.submit_command();
    }
    _ => {}
}

// During terminal cleanup, including error paths:
execute!(std::io::stdout(), DisableBracketedPaste)?;
```

Bracketed paste makes a supporting terminal wrap the paste so Crossterm produces **one `Event::Paste(String)`**, including its newlines. Ensure your Crossterm version has bracketed-paste support enabled and your event dispatcher forwards paste events.

Avoid blindly replacing newlines with spaces: that can change shell comments, heredocs, and command semantics. For a single-line input, rejecting multiline pastes is a straightforward default.

Verify that a multiline paste executes **zero commands**, a single-line paste waits for Enter, and ordinary Enter still submits once. Terminals without bracketed-paste support cannot reliably distinguish paste from typing; timing heuristics aren’t a dependable fix.

The workspace is empty, so I couldn’t inspect or patch your implementation.