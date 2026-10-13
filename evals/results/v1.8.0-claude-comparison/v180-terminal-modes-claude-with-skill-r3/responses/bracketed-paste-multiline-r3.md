## What's going on

Your app isn't turning on **bracketed paste**, so it can't tell a paste apart from typing.

- Crossterm leaves bracketed paste (DEC mode 2004) off by default, and `ratatui::init()` / `ratatui::run()` don't turn it on.
- With it off, the terminal sends pasted text as if it were typed. Each newline arrives as a carriage return, which crossterm reports as `KeyCode::Enter`.
- Your input's Enter handler can't tell a pasted newline from a real Enter key, so it submits after every line. A three-line snippet becomes three commands. A snippet with a `\` line continuation or a heredoc becomes broken partial commands, which is the dangerous part.

With mode 2004 on, the terminal wraps the paste in `ESC[200~ … ESC[201~` and crossterm delivers the whole thing as one `Event::Paste(String)`. Pasted text then never reaches your Enter handler.

## The fix

### 1. Turn on bracketed paste, and turn it off on every exit path

`ratatui::restore()` only undoes raw mode and the alternate screen. You have to undo anything you turned on yourself, including on panic and when you hand the terminal to a child process.

```rust
use std::io::stdout;
use ratatui::crossterm::{execute, event::{EnableBracketedPaste, DisableBracketedPaste}};

fn main() -> color_eyre::Result<()> {
    color_eyre::install()?;
    let mut terminal = ratatui::init();
    execute!(stdout(), EnableBracketedPaste)?;

    // ratatui's panic hook restores raw mode + alt screen only; add paste mode
    let hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        let _ = execute!(stdout(), DisableBracketedPaste);
        hook(info);
    }));

    let result = App::default().run(&mut terminal);
    let _ = execute!(stdout(), DisableBracketedPaste);
    ratatui::restore();
    result
}
```

If you hand off to `$EDITOR` or a subshell, send `DisableBracketedPaste` before `restore()` and send `EnableBracketedPaste` again when you re-enter.

### 2. Handle `Event::Paste` separately from key events

```rust
match event::read()? {
    Event::Paste(text) => self.input.paste(&text),   // never submits
    Event::Key(key) if key.kind == KeyEventKind::Press => self.handle_key(key),
    _ => {}
}
```

```rust
fn paste(&mut self, raw: &str) {
    // terminals send CR or CRLF; strip control chars rather than trusting the terminal to
    let text: String = raw.replace("\r\n", "\n").replace('\r', "\n")
        .chars().filter(|&c| c == '\n' || c == '\t' || !c.is_control()).collect();
    if text.contains('\n') {
        self.enter_multiline(text);           // see policy below
    } else {
        self.insert_at_cursor(&text);
    }
}
```

The control-character filter matters. xterm, kitty, Ghostty and foot neutralize escape sequences inside a paste, but not every terminal does. Without the filter, a crafted clipboard could inject keystrokes.

### 3. Decide what a multi-line paste means

The one fixed rule is that **a paste never submits**. Within that, I'd pick this for a command input that people paste shell snippets into:

- **Recommended:** grow the input into a multi-line review box using `ratatui-textarea` (the Ratatui org's maintained fork; install it from crates.io, not a random GitHub fork). Show the snippet with a hint like `4 lines · Alt+Enter run · Esc cancel`.
  - Ctrl+S also works as the run key, since raw mode delivers it as a normal keypress.
  - Avoid Ctrl+Enter as the only run key: without the kitty keyboard protocol it looks the same as Enter, and tmux usually strips it.
  - Run the snippet as **one script**, e.g. `sh -c "$snippet"` or the whole thing written to the shell's stdin. Don't split it into lines yourself, or continuations and heredocs break again.
  - Cap the box at about 6–8 rows and scroll inside it. At 80×24 that still leaves the output pane over half the screen, and in a 60-column tmux split the long lines truncate horizontally rather than wrap.
- **If you want to stay single-line:** keep the first line, put the cursor at the end, and show `Pasted 4 lines, kept line 1`. Or refuse the paste with that message. Don't silently drop the rest.

### 4. Fallback for terminals without mode 2004

Some terminals and setups never send bracketed paste, such as some older terminals and the legacy Windows console; I'd also expect crossterm to return an error for `EnableBracketedPaste` on the legacy Windows API, so check that. For those, add a heuristic: when Enter arrives and `event::poll(Duration::ZERO)?` shows more input already waiting, treat it as a pasted newline instead of a submit. People can't type that fast, but a paste always arrives that way. Treat this as a backstop only; the real fix is step 1.

## Tests

- **Unit tests** (cheapest): feed `Event::Paste("echo a\necho b".into())` into your update logic. Assert that nothing was submitted and the input is in multi-line mode (or kept line 1 with a notice). Add cases for CRLF and for embedded `\x1b`.
- **Unit test the fallback:** a synthetic Enter while more input is queued should not submit.
- **One PTY smoke test:** write `\x1b[200~echo a\necho b\x1b[201~` to the pty and assert one pending command, zero commands run. After the app exits, check that the terminal is no longer in mode 2004 (i.e. it received `ESC[?2004l`).

I haven't seen your input code, so if your Enter handling is spread over several places, show me the event loop and I'll point to where the paste branch should go.
