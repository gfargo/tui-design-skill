On every exit, send two sequences yourself, because `ratatui::restore()` resets neither one:

1. **Cursor:** reset the shape with `CSI 0 SP q` (`\x1b[0 q`). In crossterm this is `SetCursorStyle::DefaultUserShape`.
2. **Title:** don't just overwrite it. Save the user's title with `CSI 22;0t` at startup, before your first `SetTitle`. Then restore it with `CSI 23;0t` on exit. crossterm has `SetTitle` but no command for saving or restoring, so write these bytes directly.

Run this cleanup on every exit path: normal quit, a returned error, a panic, and any temporary handoff to a shell or editor.

```rust
use std::io::{stdout, Write};
use ratatui::crossterm::{execute, cursor::SetCursorStyle, terminal::SetTitle};

const PUSH_TITLE: &str = "\x1b[22;0t";
const POP_TITLE: &str  = "\x1b[23;0t";

fn enter_chrome(file: &str) -> std::io::Result<()> {
    let mut out = stdout();
    out.write_all(PUSH_TITLE.as_bytes())?;            // save the user's title first
    execute!(out, SetTitle(file))
}

fn leave_chrome() {
    let mut out = stdout();
    // Best-effort: run both even if one fails.
    let _ = execute!(out, SetCursorStyle::DefaultUserShape); // CSI 0 SP q
    let _ = out.write_all(POP_TITLE.as_bytes());
    let _ = out.flush();
}

fn main() -> color_eyre::Result<()> {
    color_eyre::install()?;
    // Install this hook before ratatui::init(), so Ratatui's own hook wraps it:
    // on panic, Ratatui restores, then leave_chrome runs, then the report prints.
    let report = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| { leave_chrome(); report(info); }));

    let mut terminal = ratatui::init();
    enter_chrome(&file_name)?;
    let result = App::new().run(&mut terminal);   // keep the result; no `?` here
    ratatui::restore();
    leave_chrome();
    result
}
```

**Things to cover:**

- **Panics:** use the hook, not a `Drop` guard. `Drop` doesn't run under `panic = "abort"`, but the hook does.
- **Suspend and editor handoff (Ctrl+Z, `:!sh`, spawning `$EDITOR`):** call `leave_chrome()` after `ratatui::restore()`, before handing off. After you take the terminal back, call `enter_chrome()` again and set the cursor shape to match the current mode. Otherwise the shell or child program gets your bar cursor and file title.
- **SIGTERM:** turn it into a quit event so the program leaves the loop through the code above. Default SIGTERM never runs Rust cleanup.

**Limits in some terminals:**

- **Cursor:** the current shape can't be read, so you can't save it, only reset it. Windows Terminal, foot and Ghostty treat `0` as the user's configured cursor. xterm treats it as a blinking block. xterm patch 411 and later can restore the user's own choice with `CSI 7 SP q`, so send that too if xterm users matter to you.
- **Title:** xterm, kitty, foot, iTerm2, Alacritty and tmux support saving and restoring the title. WezTerm, Ghostty and Windows Terminal ignore those sequences, so the user's original title can't be recovered there. In those terminals, check `TERM_PROGRAM` or `WT_SESSION` and send `SetTitle("")` instead of the restore. An empty title beats a stale file name, and many shell prompts (starship, oh-my-zsh, fish) set the title again on the next prompt anyway.
- **Keep the title if it's useful:** setting the title is reasonable when it helps users find the window, so keep it.

**How to test it:** run the editor in a real terminal (a PTY) and check three exits: a clean `:q`, a returned error, and a forced `panic!()`. Do each from insert mode, and confirm the shell gets back its normal cursor and the original title. Repeat in one terminal that supports saving the title (kitty or tmux) and one that doesn't (WezTerm or Ghostty).
