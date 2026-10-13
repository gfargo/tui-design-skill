I checked the working directory and it's empty, so I can't see your code. This answer covers the usual cause in Ratatui apps. If you share the event loop, I can point to the exact lines to change.

## What's going on

When bracketed paste is off, the terminal doesn't tell the app that a paste happened. It types the pasted text into the app one character at a time, as if the user were typing very fast. Each newline in the pasted text comes through as a carriage return (`\r`). Crossterm reads that as `KeyCode::Enter`, which is the same event as the user pressing Enter.

So pasting this:

```
cd /tmp
rm -rf build
make
```

reaches your input handler as `c`, `d`, ` `, … `Enter`, `r`, `m`, … `Enter`, `m`, `a`, `k`, `e`. The Enter handler submits whatever is in the buffer, so each line runs as its own command. Your input widget isn't doing anything wrong. It just has no way to tell a pasted newline from a real Enter key.

This is also a safety problem, not only a UX bug. A web page can hide a newline or extra commands in text the user copies (known as "pastejacking"), and your app would run them without asking.

## The fix: turn on bracketed paste and handle `Event::Paste`

When bracketed paste is on, the terminal wraps pasted text in `ESC[200~ … ESC[201~`. Crossterm then delivers the whole paste as one `Event::Paste(String)` instead of separate key events.

**1. Enable it at startup and disable it on every exit path, including panics:**

```rust
use crossterm::{
    event::{DisableBracketedPaste, EnableBracketedPaste},
    execute,
    terminal::{EnterAlternateScreen, LeaveAlternateScreen},
};

fn setup() -> io::Result<()> {
    crossterm::terminal::enable_raw_mode()?;
    execute!(io::stdout(), EnterAlternateScreen, EnableBracketedPaste)?;
    Ok(())
}

fn restore() -> io::Result<()> {
    execute!(io::stdout(), DisableBracketedPaste, LeaveAlternateScreen)?;
    crossterm::terminal::disable_raw_mode()
}
```

If you use `ratatui::init()` / `ratatui::restore()`, those don't enable bracketed paste. You need to add the `execute!` calls yourself and also add `DisableBracketedPaste` to your panic hook. If you don't, the user's shell is left in bracketed-paste mode after a crash, and their pastes show up as `^[[200~…`.

**2. Handle the paste as one event, and don't let it submit anything:**

```rust
match event::read()? {
    Event::Paste(text) => app.input.insert_paste(&text),
    Event::Key(key) if key.kind == KeyEventKind::Press => match key.code {
        KeyCode::Enter => app.submit(),
        // ...
    },
    _ => {}
}
```

**3. Decide what to do with the newlines.** The input is single-line, so the pasted text has to be changed before it goes into the buffer. Options, from safest to least safe:

- **Insert it and replace each newline with a visible marker** (for example `⏎`), then show a warning such as "multi-line paste: Enter runs the whole paste as one script." This is the safest choice, because the user sees everything before anything runs.
- **Join the lines with `; ` or ` && `.** This is convenient, but you're making a decision for the user: `&&` stops at the first failure and `;` keeps going. Only do this if your commands go through a shell.
- **Strip a single trailing newline.** Do this in every case. Copying a whole line often picks up the newline at the end, and nobody expects that to count as Enter.
- **Reject it or ask first** if the paste has more than one non-empty line.

Whichever you choose, a paste should never trigger a submit by itself. Only an actual Enter key press should.

```rust
fn insert_paste(&mut self, text: &str) {
    let text = text.strip_suffix('\n').unwrap_or(text);
    let text = text.replace("\r\n", "\n").replace('\r', "\n");
    if text.contains('\n') {
        self.multiline_warning = true;
    }
    self.insert_str(&text.replace('\n', " ⏎ ")); // or your chosen policy
}
```

If you use `tui-input` or `tui-textarea`, check how it handles paste. `tui-textarea` has `insert_str`, which keeps the newlines, so you'd still need to clean the text up first for a single-line field.

## Caveats

- **Windows:** crossterm's Windows backend doesn't emit `Event::Paste`, so pastes still arrive as key events there. If you support Windows, add a fallback: when an Enter arrives while more input is already waiting (`event::poll(Duration::ZERO)` returns `true` right away), treat it as a pasted newline rather than a submit. Real typing is never that fast.
- **Terminal support:** almost every modern terminal and tmux supports bracketed paste. A few old or minimal terminals don't, and the same fallback covers them.
- **Feature flag:** `Event::Paste` depends on crossterm's `bracketed-paste` feature. It's on by default, so only check it if you turned off default features.

If you send me the file with your event loop and input handling, I can write the actual patch.
