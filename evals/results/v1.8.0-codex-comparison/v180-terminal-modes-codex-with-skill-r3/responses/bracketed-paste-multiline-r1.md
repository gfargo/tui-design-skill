**Enable bracketed paste and handle pasted text separately from keypresses.** Using the tui-design skill’s Rust and input-protocol guidance: this is an input handling problem, rather than a Ratatui rendering problem.

Without bracketed paste, the terminal sends pasted text much like typing. Pasted newlines can arrive as Enter key events, so your “Enter → execute” handler runs each line. Raw mode does not prevent this; Ratatui/Crossterm do not enable bracketed paste by default.

With bracketed paste enabled, supporting terminals wrap the clipboard contents in `ESC[200~` … `ESC[201~`, and Crossterm delivers an `Event::Paste(String)`.

```rust
use std::io::stdout;
use ratatui::crossterm::{
    execute,
    event::{
        DisableBracketedPaste, EnableBracketedPaste,
        Event, KeyCode, KeyEventKind,
    },
};

// During terminal setup:
execute!(stdout(), EnableBracketedPaste)?;

// In your event handler:
match event {
    Event::Paste(text) => {
        if text.contains('\n') || text.contains('\r') {
            app.set_status("Multiline paste rejected; enter one command.");
        } else {
            app.insert_text(&text); // Insert at cursor; never execute here.
        }
    }
    Event::Key(key)
        if key.kind == KeyEventKind::Press
            && key.code == KeyCode::Enter =>
    {
        app.submit_command();
    }
    _ => {}
}

// During terminal cleanup:
execute!(stdout(), DisableBracketedPaste)?;
```

The `app` methods above are illustrative. Preserve `Event::Paste` through your event channel; an input layer that forwards only `Event::Key` will discard it.

For a **single-line command field, reject the entire multiline paste with a visible message**, leaving the existing input untouched. Keeping only the first line is another option, but shell snippets often contain continuations or here-documents, making rejection clearer. Don’t silently replace newlines with spaces—it can change shell semantics. If multiline scripts are intended, offer a multiline editor and an explicit Run action.

Disable paste mode on normal exit, errors, panic cleanup, and temporary shell/editor handoff; re-enable it when the TUI resumes. Don’t assume `ratatui::restore()` cleans up modes you enabled yourself.

Verify that:

- A multiline `Event::Paste`, including CRLF and a trailing newline, executes **zero** commands.
- A single-line paste inserts text and waits for a separate Enter press.
- A real-terminal paste arrives as `Event::Paste`, including through your supported tmux/SSH setup.

If a terminal does not support or forward bracketed paste, ordinary input events cannot reliably distinguish pasted Enter from typed Enter. Timing heuristics are not a dependable fix.