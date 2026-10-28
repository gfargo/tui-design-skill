You need two fixes. Ratatui doesn't do inline mode through `run()`, and the stray prompt comes from where the cursor is left when you quit.

## 1. Use `init_with_options` instead of `run()`

`ratatui::run()` and `ratatui::init()` always switch to the alternate screen, which is why your picker takes over the terminal. To run inline:

- Call `ratatui::init_with_options`. It turns on raw mode and installs the panic-restore hook, but it doesn't switch to the alternate screen.
- Pass `Viewport::Inline(n)`. This reserves `n` rows under the prompt.

Don't build the terminal by hand. Doing that drops the panic hook, so a panic would leave your shell in raw mode.

```rust
use ratatui::{backend::Backend, Terminal, TerminalOptions, Viewport};

fn main() -> std::io::Result<()> {
    let options = TerminalOptions { viewport: Viewport::Inline(10) };
    let mut terminal = ratatui::init_with_options(options); // raw mode + panic hook, no alt screen
    let result = run(&mut terminal);     // keep the result; don't `?` past cleanup
    let _ = erase_inline(&mut terminal); // or skip this to keep the last frame (see below)
    ratatui::restore();
    result
}
```

Inside `draw`, lay out from `frame.area()`, never `Rect::new(0, 0, ..)`. An inline viewport starts wherever the cursor was, not at row 0.

## 2. Leave the cursor where the shell expects it

When an inline app exits, its last frame stays on screen and the cursor sits at the end of the last cell. That's why your prompt printed on your UI's last line. Choose one of these:

**Option A: erase the picker (usual for a picker).** `Terminal::clear()` alone isn't enough, because it puts the cursor back where it was before the clear. Move the cursor back to the viewport's top-left corner yourself:

```rust
/// Erase a transient UI and leave the cursor where it began.
fn erase_inline<B: Backend>(terminal: &mut Terminal<B>) -> Result<(), B::Error> {
    let origin = terminal.get_frame().area().as_position();
    terminal.clear()?;
    terminal.set_cursor_position(origin)
}
```

After this, the prompt comes back exactly where the picker started, and nothing is left behind.

**Option B: keep the last frame.** Leave out `erase_inline` and call `println!()` after `ratatui::restore()`. That moves the cursor to a new line so the prompt doesn't join the frame.

## 3. Think about stdout if this will be used as `$(picker)`

A picker like this usually prints the chosen path to stdout, so you can write `vim "$(picker)"` or `cd "$(picker)"`. But `init_with_options` draws to stdout, so command substitution would capture the UI too and the user would see nothing. If you want that usage:

- Draw the UI on stderr: `Terminal::with_options(CrosstermBackend::new(std::io::stderr()), options)`.
- Enable and disable raw mode yourself.
- Install a panic hook yourself that disables raw mode before the default hook runs.
- After cleanup, print only the selected path to stdout. Exit with a non-zero code if the user cancels, so scripts can tell nothing was chosen.

On Unix, crossterm reads keys from `/dev/tty` when stdin isn't a terminal, so input still works inside `$(...)`.

## Quick checks

- **Height:** 8–12 rows is typical. If the prompt is near the bottom of the screen, Ratatui scrolls the terminal up to make room.
- **Exits:** test Enter (select), Esc and Ctrl+C (cancel), and a deliberate panic. Each one should leave a clean prompt with the cursor at column 0 and echo working. If you turn on extra modes such as mouse capture or bracketed paste, turn them off before `restore()`, because `restore()` only undoes raw mode.
- **Permanent lines:** if you want lines to stay above the picker (for example "copied 3 files"), use `terminal.insert_before(...)` and turn on Ratatui's `scrolling-regions` feature so the viewport doesn't flicker.
