This is usually **paste being interpreted as typing**. Without bracketed paste enabled, the terminal sends pasted text through the normal input stream. Each newline can become an Enter key event, which triggers your command submission handler.

Ratatui renders the interface; your terminal backend and event handling control this behavior. The workspace here is empty, so I can’t verify your implementation.

For a Crossterm-backed app, enable **bracketed paste** during terminal setup:

```rust
use crossterm::{
    execute,
    event::{
        self, DisableBracketedPaste, EnableBracketedPaste,
        Event, KeyCode, KeyEventKind,
    },
};

// During terminal setup:
execute!(std::io::stdout(), EnableBracketedPaste)?;
```

Supporting terminals will then wrap pasted text in special delimiters, and Crossterm will deliver the whole payload as `Event::Paste(String)`, including its newlines. Handle that separately from key events:

```rust
match event::read()? {
    Event::Paste(text) => {
        if text.contains('\n') || text.contains('\r') {
            // Single-line policy: reject the entire paste.
            app.set_status("Multi-line paste rejected; paste one command.");
        } else {
            app.insert_text(&text);
        }
        // Never submit from this branch.
    }

    Event::Key(key) if key.kind == KeyEventKind::Press => {
        match key.code {
            KeyCode::Enter => app.submit_command(),
            _ => app.handle_key(key),
        }
    }

    _ => {}
}
```

The `app` methods above are illustrative. Disable bracketed paste during terminal cleanup, including error and panic cleanup:

```rust
execute!(std::io::stdout(), DisableBracketedPaste)?;
```

For the input policy, choose one of these deliberately:

- **Strict single-line input:** reject the entire multiline paste and show a message.
- **Multiline support:** preserve the original text in a buffer, display a reviewable preview, and execute only after an explicit submit action.

**Don’t blindly replace newlines with spaces or semicolons.** That can change shell meaning, especially with comments, quoted strings, continuations, and heredocs.

Verify that single-line paste only inserts text, multiline paste never executes anything, CRLF is handled, and a subsequent Enter submits at most once. Also test your terminal and any tmux/SSH setup: if bracketed paste isn’t supported, ordinary input events cannot reliably distinguish pasted newlines from typed Enter. Timing heuristics won’t reliably fix that.