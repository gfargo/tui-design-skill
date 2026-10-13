Yes. The feature is **synchronized output**, DEC private mode 2026. It's the right fix, and both kitty and WezTerm support it. You put `CSI ? 2026 h` before a frame and `CSI ? 2026 l` after it. The terminal holds the frame and paints it all at once, so it never shows a half-drawn table.

Ratatui doesn't send this for you; it's the app's job. Bubble Tea, Textual and Ink handle it themselves, but Ratatui and crossterm leave it to you. Crossterm already has the two commands: `BeginSynchronizedUpdate` and `EndSynchronizedUpdate`.

## Using it safely

The main risk is **sending Begin without a matching End**. The terminal then freezes on that frame until its own timeout runs out: 2 s in kitty, 1 s in Ghostty, 150 ms in Alacritty. Your app looks hung during that time. Every path out of a frame has to send End, including errors and panics.

### 1. Wrap each draw, and send End even when the draw fails

```rust
use std::io::stdout;
use ratatui::crossterm::{execute, queue, terminal::{BeginSynchronizedUpdate, EndSynchronizedUpdate}};

fn draw_synced(terminal: &mut DefaultTerminal, app: &App) -> std::io::Result<()> {
    queue!(stdout(), BeginSynchronizedUpdate)?;
    let drawn = terminal.draw(|f| app.draw(f)).map(|_| ());
    let ended = execute!(stdout(), EndSynchronizedUpdate); // always runs; no `?` above it
    drawn.and(ended)                                       // report the draw error first
}
```

Use this in place of `terminal.draw(...)` in your loop. Don't put `?` on the draw call: that would return early and skip End.

### 2. Send End from the panic hook

Ratatui's `restore()` only undoes raw mode and the alternate screen. It won't close a frame that a panic left open (for example, a panic inside `app.draw`). Chain a hook **after** `ratatui::init()` so it runs before Ratatui's restore:

```rust
let mut terminal = ratatui::init();
let prev = std::panic::take_hook();
std::panic::set_hook(Box::new(move |info| {
    let _ = execute!(stdout(), EndSynchronizedUpdate);
    prev(info); // Ratatui's restore, then color_eyre's report
}));
```

A `Drop` guard wouldn't help if you build with `panic = "abort"`, and it doesn't run at all on SIGKILL. The hook plus always sending End covers the cases you can actually control.

### 3. Feature detection

You can check support properly with DECRQM (`CSI ? 2026 $ p`), but crossterm won't parse the reply, so you'd have to read it from the input stream yourself, with a timeout. Most apps skip that and send the sequences unconditionally on a TTY, which is what Ink does. A terminal that doesn't know mode 2026 just ignores it. Don't send it when output isn't a TTY.

## Environments where it won't help

- **tmux before 3.7** won't pass it through, so you'll still see tearing inside those sessions. tmux 3.7+ supports it.
- **Terminals without it** need the usual fallbacks: send each frame in as few writes as possible, send only changed cells, and hide the cursor while drawing. Ratatui already diffs cells and hides the cursor. One limit to know: by default `ratatui::init()` writes to Rust's `Stdout`, which buffers lines through a small internal buffer. A large table frame can therefore go out in many small writes. If you need to fix that, build the terminal yourself on a large `BufWriter`. You then have to set up raw mode, the alternate screen and the panic hook yourself.

## Check why so much is being redrawn

Synchronized output hides tearing, but it doesn't reduce the number of bytes sent. Ratatui only sends cells that changed, so a large table that tears every tick usually means one of these:

- **`terminal.clear()` called every tick.** This forces a full repaint. Only use it after a handoff, such as returning from an external editor.
- **Redrawing on every tick when nothing changed.** Draw only when there's input, new data, a resize or an animation you actually want. Have `on_tick` return a "dirty" flag.
- **Every row changing on every tick.** Examples are a ticking relative timestamp ("3s ago") in each row, or a row order that keeps shifting because the sort isn't stable. Update those values less often, or move them to a status line.
- **Rendering every row.** Use `Table` with `TableState` so only the visible rows are rendered.

## How to verify

1. Run it in kitty and WezTerm and check that the tearing is gone.
2. Make `app.draw` return an error, and separately make it panic. In both cases the terminal should recover immediately, not stall for about 2 s.
3. Run it inside tmux 3.7+ and inside an older tmux to see which behaviour your users will get.

If you share the table layout, I can also count how much of the screen is borders and repeated text, and check how it holds up at 80×24 and in a 60-column split. Big tables often have redundant row markers or timestamps that change every tick, and those make the redraw cost worse.
