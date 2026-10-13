I've read the skill's Rust and terminal-input references and have the cause and the fix.

## What's going on

In raw mode, the terminal sends pasted text exactly as if it were typed. It doesn't mark where the paste starts or ends. Each newline in the clipboard arrives as a carriage return, which crossterm reports as `KeyCode::Enter`. Your Enter handler submits the line, so a 4-line snippet becomes 4 separate submits.

The terminal can tell you when text was pasted, using **bracketed paste mode (DECSET 2004)**. It wraps the paste in `ESC[200~ … ESC[201~`, and crossterm turns that into a single `Event::Paste(String)`. But crossterm doesn't turn this mode on by default, and neither do `ratatui::init()` and `ratatui::run()`. So your app sees a stream of keypresses instead.

## The fix

### 1. Turn bracketed paste on, and always turn it off again

`ratatui::restore()` only undoes raw mode and the alternate screen. It won't undo modes you turn on yourself. Use a drop guard so the mode is turned off on normal exit, on returned errors, and when a panic unwinds:

```rust
use std::io;
use ratatui::crossterm::{execute, event::{EnableBracketedPaste, DisableBracketedPaste}};

struct BracketedPaste;
impl BracketedPaste {
    fn enable() -> io::Result<Self> {
        execute!(io::stdout(), EnableBracketedPaste)?;
        Ok(Self)
    }
}
impl Drop for BracketedPaste {
    fn drop(&mut self) {
        let _ = execute!(io::stdout(), DisableBracketedPaste);
    }
}

fn main() -> color_eyre::Result<()> {
    color_eyre::install()?;
    ratatui::run(|terminal| {
        // Not fatal if unsupported (e.g. legacy Windows console); see fallback below.
        let _paste = BracketedPaste::enable().ok();
        App::default().run(terminal)
    })
}
```

Don't add another restore panic hook on top of `ratatui::run()`, because it already installs one. If you build with `panic = "abort"`, drop guards never run, so you'd have to turn the mode off from a panic hook instead.

### 2. Handle `Event::Paste` as one event, and never submit from it

```rust
match event::read()? {
    Event::Key(key) if key.kind == KeyEventKind::Press => self.on_key(key),
    Event::Paste(text) => self.on_paste(&text),
    _ => {}
}

fn on_paste(&mut self, raw: &str) {
    // Normalize CRLF/CR, and drop control chars: not every terminal neutralizes ESC inside a paste.
    let text: String = raw.replace("\r\n", "\n").replace('\r', "\n")
        .chars().filter(|c| *c == '\n' || *c == '\t' || !c.is_control()).collect();
    let text = text.trim_end_matches('\n');

    if !text.contains('\n') {
        self.input.insert_str(text);   // ordinary single-line paste
    } else {
        self.pending_paste = Some(text.to_owned());
        self.status = format!(
            "Pasted {} lines. Enter: run as one script · e: keep first line · Esc: discard",
            text.lines().count()
        );
    }
}
```

The one rule: **a paste into a single-line field must never submit.** Either keep the first line or hold the paste and ask, as above. I'd hold and ask here, because someone pasting a shell snippet probably does want to run it, but they should do it with one deliberate keypress. Running it as one script (or joining the lines with `&&`) also keeps the snippet's meaning. Running each line separately can change it, since a `cd` or an `export` in one line won't carry over to the next. If you add a multi-line editor later (e.g. `tui-textarea`), the "Enter" option could open the paste there instead.

### 3. Fallback when you never get `Event::Paste`

On Windows, crossterm reads console input records rather than escape sequences, so you shouldn't count on `Event::Paste` there. Some terminals and multiplexers may also not pass the mode through. A common workaround: when Enter arrives and more input is already waiting (`event::poll(Duration::ZERO)? == true`), insert a newline into a pending buffer instead of submitting. Pasted text arrives in a burst; a human pressing Enter doesn't. This is a guess, not a guarantee, so keep it as the fallback and rely on bracketed paste where it works.

## Tests

1. **Unit tests (most coverage):** call `on_paste` directly with `"echo a\necho b"`, `"echo a\r\necho b\r\n"`, a single line, and text containing `\x1b`. Check that nothing was submitted, that `pending_paste` and the status line are set, and that single-line pastes are inserted at the cursor.
2. **Key-handling test:** send `Event::Paste` followed by a real Enter key event. Check that only the explicit Enter runs anything, and only once.
3. **One PTY smoke test:** write `\x1b[200~echo a\necho b\x1b[201~` to the app and check that nothing ran. Then exit normally, and also force a panic. Both times, check that the output includes `\x1b[?2004l` so the user's shell isn't left in paste mode.
