I looked in the working directory but it's empty, so I couldn't read your input code. This explanation is based on how terminals and crossterm work, and the cause is almost always the same.

## What's going on

When you paste into a terminal, the terminal doesn't send one "paste" event by default. It sends the clipboard text into the PTY as if it were typed, one character at a time. A newline in the pasted text reaches your app as `\r`. crossterm reads that as `KeyCode::Enter`, which looks exactly like the user pressing Enter. Your input handler sees `e`, `c`, `h`, `o`, …, `Enter`, `l`, `s`, `Enter`, and submits after every line.

This is also a safety problem, not just an annoyance. Pasting something with a trailing newline runs it before the user has a chance to look at it.

## The fix: turn on bracketed paste

Most modern terminals support **bracketed paste mode**. Once your app turns it on, the terminal wraps pasted text in `ESC[200~ … ESC[201~` markers. crossterm then delivers the whole paste as a single `Event::Paste(String)` instead of a stream of keys.

**1. Turn it on at startup and off on exit, including when the app panics:**

```rust
use crossterm::{
    event::{EnableBracketedPaste, DisableBracketedPaste},
    execute,
    terminal::{enable_raw_mode, disable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};

fn setup_terminal() -> io::Result<()> {
    enable_raw_mode()?;
    execute!(io::stdout(), EnterAlternateScreen, EnableBracketedPaste)?;
    Ok(())
}

fn restore_terminal() -> io::Result<()> {
    execute!(io::stdout(), DisableBracketedPaste, LeaveAlternateScreen)?;
    disable_raw_mode()
}

// In main, before the event loop, so a panic doesn't leave the user's shell in paste mode:
let hook = std::panic::take_hook();
std::panic::set_hook(Box::new(move |info| {
    let _ = restore_terminal();
    hook(info);
}));
```

If you use `ratatui::init()` / `ratatui::restore()`, they handle raw mode and the alternate screen but **not** bracketed paste. You still need to add `EnableBracketedPaste` and `DisableBracketedPaste` yourself.

**2. Handle `Event::Paste` as text insertion, never as a submit:**

```rust
match event::read()? {
    Event::Paste(text) => app.input.insert_str(&sanitize_paste(&text)),
    Event::Key(key) if key.kind == KeyEventKind::Press => match key.code {
        KeyCode::Enter => app.submit(),
        // ...
        _ => {}
    },
    _ => {}
}
```

**3. Decide what a multi-line paste should mean.** The input is single-line, so you need a rule:

```rust
fn sanitize_paste(s: &str) -> String {
    let s = s.replace("\r\n", "\n");
    let s = s.trim_end_matches('\n');           // never auto-run because of a trailing newline
    s.chars()
        .filter(|c| !c.is_control() || *c == '\n' || *c == '\t')  // drop stray escape/control chars
        .map(|c| if c == '\t' { ' ' } else { c })
        .collect::<String>()
        .replace('\n', " ; ")                   // or "\n" if your executor accepts multi-line input
}
```

There are three reasonable rules:
- **Join into one command**, with `; ` or `&&` between lines. This is simple but changes meaning if one line fails.
- **Keep the newlines and show a "N lines" badge** in the input, then send the whole block to the shell as one script when the user presses Enter. This is usually the best experience if your backend runs commands through `sh -c`.
- **Ask for confirmation** ("Paste 4 lines? Run as script / Cancel"). Do this if commands can be destructive.

Whichever you choose, the key rule is that a paste never submits anything. Only a real Enter key press does.

## Fallback for terminals without bracketed paste

Some environments never send `Event::Paste`: older Windows consoles (crossterm doesn't emit paste events there), some serial or embedded terminals, and certain tmux/screen setups. For those, a timing heuristic helps. A real Enter press is almost never immediately followed by more input that's already waiting, so if more input is queued, treat the Enter as part of a paste:

```rust
KeyCode::Enter => {
    if event::poll(Duration::from_millis(0))? {
        // More input is already queued: this Enter is part of a paste, not a keypress.
        app.input.insert_char('\n'); // or ' ' / show multi-line badge
    } else {
        app.submit();
    }
}
```

## Checklist
- `EnableBracketedPaste` on startup; `DisableBracketedPaste` on exit **and** in the panic hook
- `Event::Paste` inserts text and never submits
- Strip trailing newlines and control characters from pasted text
- Choose a rule for multi-line pastes (join, multi-line badge, or confirm)
- Add the timing check as a fallback for terminals without bracketed paste

If you point me to the event loop and input widget code, I can make these changes in place.
