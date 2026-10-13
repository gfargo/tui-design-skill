I didn't find any source code in the working directory (it's empty), so I can't point to your files. This is a well-known problem, though, and the cause and fix are almost always the same.

## What's going on

When bracketed paste is off, the terminal sends pasted text to your app as if it were being typed. Each character arrives as a separate key event, and each newline in the paste arrives as `Enter` (usually `\r` → `KeyCode::Enter`). Your input handler can't tell a pasted newline from a real Enter press, so it runs the command, clears the buffer, and starts collecting the next line.

## The fix: turn on bracketed paste and handle paste events separately

With bracketed paste on, the terminal wraps pasted text in `ESC[200~ … ESC[201~` markers. Crossterm reads these markers and gives you the whole paste as **one** event, `Event::Paste(String)`, instead of a stream of key events.

**1. Enable it at startup and disable it on teardown.** Put it next to your raw mode and alternate screen calls, and include your panic hook:

```rust
use crossterm::{
    event::{EnableBracketedPaste, DisableBracketedPaste},
    execute,
};

// setup
execute!(stdout, EnterAlternateScreen, EnableBracketedPaste)?;

// restore (normal exit AND panic hook)
execute!(stdout, DisableBracketedPaste, LeaveAlternateScreen)?;
```

If you skip the disable on exit or panic, the user's shell gets stuck with stray `200~` markers on every paste.

**2. Handle `Event::Paste` as an insertion, never a submit:**

```rust
match event::read()? {
    Event::Paste(text) => app.input.insert_paste(&text),
    Event::Key(key) if key.kind == KeyEventKind::Press => match key.code {
        KeyCode::Enter => app.submit(),
        KeyCode::Char(c) => app.input.insert_char(c),
        // ...
    },
    _ => {}
}
```

**3. Choose what a multi-line paste means in a single-line input.** Normalize `\r\n` and `\r` to `\n` first, then pick one policy:

- **Join into one command (my recommendation for a shell-style input):** strip trailing newlines and join the lines with `; `, or with `&&` if a failing line should stop the rest. Lines ending in `\` are continuations, so join those with a space. Leave the result in the input for the user to review. Don't run it automatically.
- **Switch to a multi-line editor:** if the paste contains `\n`, expand the input (for example, `tui-textarea`) and let the user edit it, then submit with Enter or Ctrl+Enter.
- **Ask first:** show something like "Paste contains 4 lines. Run as a single script? [y/N]".

Any of these fixes the real hazard, which is running commands the user hasn't seen.

```rust
fn insert_paste(&mut self, text: &str) {
    let text = text.replace("\r\n", "\n").replace('\r', "\n");
    let joined = text
        .trim_end_matches('\n')
        .replace("\\\n", " ")       // shell line continuations
        .split('\n')
        .filter(|l| !l.trim().is_empty())
        .collect::<Vec<_>>()
        .join("; ");
    self.insert_str(&joined);       // insert at cursor; do NOT submit
}
```

## Fallback for terminals without bracketed paste

Most modern terminals support bracketed paste. Some still don't, including some Windows console setups and certain multiplexer or SSH configurations. For those you can add a burst heuristic: when you get `Enter`, call `event::poll(Duration::from_millis(0..5))`. If more key events are already queued, the Enter was almost certainly part of a paste, so insert a newline (or apply the join policy) instead of submitting. Treat this as a backup to bracketed paste, not a replacement.

## Checklist

- Add `EnableBracketedPaste` at startup.
- Add `DisableBracketedPaste` on exit and in the panic hook.
- Handle `Event::Paste` by inserting at the cursor, normalizing line endings, and applying your multi-line policy.
- Make sure only a real `KeyCode::Enter` key event can submit.
- Optionally, add the burst heuristic.
- Test by pasting a 3-line snippet in iTerm2/Terminal.app, inside tmux, and over SSH. tmux passes bracketed paste through when the inner app requests it.

If you point me at the input-handling code, I can make these changes there.
