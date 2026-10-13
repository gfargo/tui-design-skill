This is usually **paste being treated as keyboard input**. Ratatui handles rendering; your terminal event backend handles input. Without bracketed paste mode, pasted text arrives as ordinary key events, and each newline looks like Enter. Your Enter handler then submits each line.

For a Crossterm-backed app, enable bracketed paste during setup:

```rust
use crossterm::{
    event::{self, DisableBracketedPaste, EnableBracketedPaste, Event, KeyCode},
    execute,
};

execute!(std::io::stdout(), EnableBracketedPaste)?;
```

Handle pasted text separately from submission:

```rust
match event::read()? {
    Event::Paste(text) => {
        // Single-line policy: normalize newlines; never submit on paste.
        let text = text.replace("\r\n", "\n").replace('\r', "\n");
        input.push_str(&text.replace('\n', " "));
    }
    Event::Key(key) if key.code == KeyCode::Enter => {
        submit(&input)?;
    }
    // Other input handling...
    _ => {}
}
```

Disable bracketed paste when restoring the terminal, including error and panic cleanup:

```rust
execute!(std::io::stdout(), DisableBracketedPaste)?;
```

**Choose the multiline policy explicitly.** Replacing newlines with spaces is suitable for a strictly single-line field, but can change shell semantics—particularly comments, heredocs, and continuations. If you intend to support shell snippets, preserve the paste in a multiline editor and require an explicit submission action. Alternatively, reject multiline pastes with a clear message.

Verify that pasting `echo one\n echo two\n` executes nothing until the user submits. Also check your terminal and any multiplexer support bracketed paste; without it, the app generally cannot reliably distinguish pasted newlines from typed Enter.

The workspace is empty, so I couldn’t confirm your specific event handler or apply a patch.