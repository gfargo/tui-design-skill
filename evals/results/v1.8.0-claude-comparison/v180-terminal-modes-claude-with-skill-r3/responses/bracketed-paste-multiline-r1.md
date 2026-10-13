**Why it happens:** in raw mode, a paste reaches your app as ordinary keystrokes. The terminal sends each newline in the pasted text as `\r`, and crossterm reports that as `KeyCode::Enter`. Your input can't tell typing from pasting, so every line break looks like the user pressed Enter, and each line gets submitted on its own.

Crossterm, and so Ratatui, leaves **bracketed paste (DECSET 2004)** off by default, unlike Bubble Tea and Textual. When it's on, the terminal wraps the paste in `ESC[200~ … ESC[201~`, and crossterm delivers the whole thing as one `Event::Paste(String)`.

## Fix

### 1. Turn bracketed paste on, and turn it off on every exit path

`ratatui::restore()` only undoes raw mode and the alternate screen. Any mode you enable yourself, you have to disable yourself.

```rust
use ratatui::crossterm::{execute, event::{EnableBracketedPaste, DisableBracketedPaste}};

fn main() -> color_eyre::Result<()> {
    color_eyre::install()?;
    // Install before ratatui::run so its panic hook wraps this one
    let report_hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        let _ = execute!(std::io::stdout(), DisableBracketedPaste);
        report_hook(info);
    }));

    ratatui::run(|terminal| {
        // Don't fail startup if the terminal can't do it; fall back (see step 4)
        let paste_enabled = execute!(std::io::stdout(), EnableBracketedPaste).is_ok();
        let result = App::new(paste_enabled).run(terminal);
        let _ = execute!(std::io::stdout(), DisableBracketedPaste);
        result
    })
}
```

If you set up the terminal by hand instead of using `ratatui::run`/`init`, add `DisableBracketedPaste` to the cleanup and panic hook you already have.

### 2. Handle `Event::Paste` separately from key events

```rust
match event::read()? {
    Event::Paste(text) => self.handle_paste(&text),
    Event::Key(key) if key.kind == KeyEventKind::Press => self.handle_key(key),
    _ => {}
}
```

### 3. Decide what a multi-line paste means in a single-line field

The rule: a single-line field keeps the first line or refuses the paste. It never submits. For shell commands I'd **refuse with a visible message**. Keeping only the first line means one Enter later runs part of a script, which is the same bug, just one step removed.

```rust
fn handle_paste(&mut self, text: &str) {
    let text = text.replace("\r\n", "\n").replace('\r', "\n");
    let text = text.trim_end_matches('\n'); // a copied line often brings its trailing newline
    if text.contains('\n') {
        let n = text.lines().count();
        self.status = Some(format!(
            "Pasted {n} lines; command input is single-line. Nothing was run."
        ));
        return;
    }
    // Not every terminal neutralizes escapes inside a paste; strip control chars
    let clean: String = text.chars().map(|c| if c == '\t' { ' ' } else { c })
        .filter(|c| !c.is_control()).collect();
    self.input.insert_str(&clean); // at the cursor, no submit
}
```

Trimming the trailing newline matters. Without it, copying a single command from a web page still counts as "multi-line", or it auto-runs.

If users really do want to paste snippets, add a multi-line mode rather than flattening the text. For example, a key like `Ctrl+E` (or a `paste` action) could open a `ratatui-textarea` editor that already holds the pasted text, with an explicit "run" key. Joining lines with `;` or `&&` changes what the script means, so don't do that.

### 4. Fallback for terminals without bracketed paste

Some setups won't send the paste markers: the enable call failed, or a multiplexer or legacy console didn't pass it through. In those, you can treat an `Enter` that arrives in the same burst as other characters (several events already queued, with `event::poll(Duration::ZERO)` returning true) as a newline in a paste, not a submit. It's a heuristic, so use it only when `paste_enabled` is false.

## Tests

- **Unit tests:** call `handle_paste` directly with `"a\nb"`, `"a\r\nb"`, `"cmd\n"`, and text that contains `\x1b`. Assert that nothing is submitted, what the buffer holds, and what the status message says. Feeding a synthetic `Event::Paste` into your update function covers the routing.
- **One PTY smoke test:** write `\x1b[200~echo a\recho b\x1b[201~` to the PTY and assert that no command ran. Also check that the app disables 2004 on quit, on an error return, and on a panic. If the mode leaks, shells that don't enable bracketed paste themselves (and programs like `cat`) will show `^[[200~` around everything the user pastes afterwards.
