**Enable bracketed paste and handle paste as text, never as submission.** The likely cause is that pasted newlines arrive as Enter key events, triggering your command handler repeatedly.

Ratatui renders the UI; your event loop handles input. With Crossterm, bracketed paste is opt-in. A supporting terminal wraps pasted text in `ESC[200~` … `ESC[201~`, which Crossterm delivers as `Event::Paste(String)`.

Enable it during terminal setup:

```rust
use ratatui::crossterm::{
    execute,
    event::{EnableBracketedPaste, DisableBracketedPaste},
};

execute!(std::io::stdout(), EnableBracketedPaste)?;
```

Then handle paste separately from keys. For a single-line shell command field, I recommend **rejecting multiline pastes with a visible message**, leaving the existing input intact:

```rust
match event {
    Event::Paste(text) => {
        if text.contains('\n') || text.contains('\r') {
            app.message = Some(
                "Multiline paste rejected. Paste one command at a time.".into()
            );
        } else {
            app.insert_at_cursor(&text);
        }
        // Never execute from this branch.
    }
    Event::Key(key)
        if key.kind == KeyEventKind::Press
            && key.code == KeyCode::Enter =>
    {
        app.submit_command();
    }
    _ => {}
}
```

These `app` methods are illustrative. Ensure any event channel forwards `Event::Paste` instead of dropping everything except key events.

Don’t flatten shell snippets by replacing newlines with spaces or semicolons: that changes comments, quoting, continuations, and heredocs. If multiline scripts are a supported workflow, offer a multiline editor with preview and an explicit Run action.

Disable the mode on normal exit, errors, panics, suspend, and shell/editor handoff; re-enable it on return:

```rust
execute!(std::io::stdout(), DisableBracketedPaste)?;
```

Ratatui’s default restoration does not clean up this extra mode for you.

Verify that LF, CRLF, trailing-newline, and multiline pastes execute **zero commands**, while a subsequent deliberate Enter submits once. Add a real-terminal or PTY check, including tmux if supported. Without bracketed-paste support, typing and paste can be indistinguishable; timing heuristics cannot reliably fix that.

No app source was present in the workspace, so this is the diagnosis and implementation pattern rather than an applied patch.