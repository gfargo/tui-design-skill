**Enable bracketed paste and handle it as text insertion, never command submission.** The likely cause is that paste arrives as ordinary keystrokes: each pasted newline becomes Enter, and your Enter handler executes the current buffer. Ratatui renders the UI; it doesn’t protect your input handling automatically.

With Crossterm, enable paste mode during terminal setup:

```rust
use std::io::stdout;
use ratatui::crossterm::{
    execute,
    event::{EnableBracketedPaste, DisableBracketedPaste, Event},
};

execute!(stdout(), EnableBracketedPaste)?;
```

Supporting terminals then wrap pasted text in `ESC[200~` and `ESC[201~`; Crossterm delivers it as **`Event::Paste(String)`**. Preserve that event through any event channels and handle it separately from keys:

```rust
match event {
    Event::Paste(text) => {
        if text.contains('\n') || text.contains('\r') {
            app.show_input_error(
                "Multi-line paste rejected. Enter one command."
            );
        } else {
            app.insert_at_cursor(&text);
        }
        // No execution, synthetic key events, or submit action here.
    }
    Event::Key(key) => app.handle_key(key),
    _ => {}
}
```

For a single-line shell-command field, I recommend **rejecting the whole multi-line paste and leaving the existing buffer unchanged**. Keeping only the first line is another policy, but silently replacing newlines with spaces can change shell semantics, including comments, continuations, and heredocs.

Pair setup with `DisableBracketedPaste` in your cleanup path, including errors and panics. Disable it before handing the terminal to an interactive child or suspending; re-enable it on return. Don’t assume terminal restoration covers modes you enabled yourself.

Verify these behaviors:

- Multi-line and trailing-newline pastes execute **zero commands**.
- Single-line paste inserts at the cursor; a subsequent deliberate Enter submits once.
- CRLF, Unicode, and tab-containing pastes follow the same policy.
- A real terminal/PTY test confirms paste framing and cleanup, including your supported tmux setup.

Without bracketed-paste support, pasted newlines and typed Enter are indistinguishable; timing heuristics cannot reliably fix that.

Keep rejection feedback to one inline message—no extra dialog or nested border. At 80×24 and 60 columns, keep the command field and feedback visible, wrapping the message if needed.

I used the requested tui-design skill. No application source was present in the workspace, so this is an implementation recommendation rather than an applied patch.