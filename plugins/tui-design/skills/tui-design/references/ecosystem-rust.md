# Rust ecosystem — Ratatui, crossterm, Cursive, clap

Ratatui dominates Rust TUI development; thousands of crates build on it. **Current line: 0.30** (0.30.0 stable since December 2025; 0.30.2 current). 0.30 split Ratatui into a workspace of crates and added `no_std`, but the main `ratatui` crate still re-exports everything, so imports are unchanged. What bites is the crossterm-compatibility story below.

**Contents:**
- [Quick recommendation](#quick-recommendation)
- [Ratatui](#ratatui-ratatuiratatui) — [Lifecycle and terminal handoff](#lifecycle-and-terminal-handoff) (incl. panic safety) · [Inline viewport](#inline-viewport) · [Widgets](#widgets) (popups, text-input cursor) · [Layout](#layout) · [Styling](#styling)
- [Backends](#backends-crossterm-vs-termion-vs-termwiz) · [State management](#state-management-patterns) · [Async with Tokio](#async-with-tokio) · [Testing](#testing) · [Debugging](#debugging)
- [Companion crates](#companion-crates) · [Alternatives to Ratatui](#alternatives-to-ratatui) · [Pitfalls](#pitfalls) · [Notable Rust TUI apps](#notable-rust-tui-apps-to-study) · [CLI design in Rust](#cli-design-in-rust)

## Quick recommendation

| If the user wants… | Use |
|---|---|
| Modern TUI in Rust | **Ratatui + Crossterm** |
| Form-heavy app with dialogs/menus | **Cursive** (callback-driven, retained-mode) |
| React-like declarative TUI | **iocraft** (newer, hooks + JSX-style + taffy flexbox) |
| Argument parsing for CLIs | **clap** (derive API) |
| Fancy modern wizards (Clack-style) | **cliclack** |

**Default: Ratatui + Crossterm + clap + color-eyre.** Start from `cargo generate ratatui/templates` and pick one of its six templates by app size: `hello-world` for a first run, `simple` or `event-driven` for sync apps, `simple-async` or `event-driven-async` when you need Tokio, and `component` (Tokio, action channel, config, logging) only for large multi-pane apps.

---

## Ratatui (ratatui/ratatui)

**Architectural model: immediate-mode rendering.** Every frame, the application redraws the entire UI from current state. The library handles diffing between intermediate buffers and emits only changed cells — "a video codec for text."

The mental model is **"UI = f(state)"**. You manage app state, the event loop, and timing yourself. Ratatui handles the rendering math.

**Canonical app structure:**

```rust check=rust/canonical
use ratatui::{prelude::*, widgets::*, DefaultTerminal};
use ratatui::crossterm::event::{self, Event, KeyCode, KeyEventKind, KeyModifiers};
use color_eyre::Result;

fn main() -> Result<()> {
    color_eyre::install()?;            // install reporting before Ratatui wraps the hook
    ratatui::run(|terminal| App::default().run(terminal))
}

#[derive(Default)]
struct App {
    counter: i32,
    should_quit: bool,
}

impl App {
    fn run(&mut self, terminal: &mut DefaultTerminal) -> Result<()> {
        while !self.should_quit {
            terminal.draw(|frame| self.draw(frame))?;
            self.handle_events()?;
        }
        Ok(())
    }

    fn draw(&self, frame: &mut Frame) {
        frame.render_widget(
            Paragraph::new(format!("Counter: {}", self.counter))
                .block(Block::bordered().title("Demo")),
            frame.area(),
        );
    }

    fn handle_events(&mut self) -> Result<()> {
        if let Event::Key(key) = event::read()? {
            if key.kind == KeyEventKind::Press {
                match key.code {
                    KeyCode::Char('q') | KeyCode::Esc => self.should_quit = true,
                    // raw mode delivers Ctrl+C as a key event, not SIGINT
                    KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                        self.should_quit = true
                    }
                    KeyCode::Char('+') | KeyCode::Right => self.counter += 1,
                    KeyCode::Char('-') | KeyCode::Left => self.counter -= 1,
                    _ => {} // Ctrl+Z lands here and is silently ignored; see Foreground suspend
                }
            }
        }
        Ok(())
    }
}
```

`ratatui::run()` calls `init()`, runs your closure, then `restore()`. `init()` enables raw mode, enters the alt screen, builds a `Terminal<CrosstermBackend>`, and installs a panic hook that restores the terminal before delegating to the hook already installed, so install reporting hooks such as `color_eyre` **before** it. Use `init()` / `restore()` yourself only when you need code between setup and teardown. `restore()` undoes only raw mode and the alternate screen; mouse capture, bracketed paste, and keyboard-enhancement flags stay on (see [Lifecycle](#lifecycle-and-terminal-handoff)).

### Lifecycle and terminal handoff

Ratatui owns rendering and terminal setup, but not the application event loop, subprocesses, or general process-signal policy. Prefer the managed API and make every external lifecycle event converge on the loop boundary. A bad exit leaves the user in raw mode on the alt screen with no cursor, so install any reporting hook (`color_eyre`) first and let `run()` / `init()` wrap it.

| Boundary | Ratatui 0.30 contract |
|---|---|
| Normal exit | Prefer `ratatui::run(...)`; it initializes, runs the closure, and restores afterward. With `init()` / `restore()`, retain the loop result, restore, then return the result so errors cannot skip cleanup. `restore()` covers only raw mode and the alternate screen; tear down any extra modes first (see *Extra modes* below). |
| SIGTERM | Ratatui does not turn process signals into application events. Use the runtime or a signal integration to send a quit event or cancellation into the loop, then let the closure return through managed cleanup. Default SIGTERM and SIGKILL do not unwind Rust cleanup code. |
| Interactive child | Stop the input reader first (a still-running reader steals the child's keystrokes and terminal capability responses), restore, run and wait for the child, reinitialize, clear, and redraw. Keep the child's result; if child and reentry both fail, report both instead of letting `?` discard one. See the snippet below. |
| Foreground suspend | Ratatui and Crossterm have no suspend support, and in raw mode Ctrl+Z is just a key event, so you must bind it yourself. On Unix, use the same temporary-handoff sequence, send SIGTSTP only after restoration, then reinitialize and redraw after SIGCONT (snippet below). Windows has no job control: offer a drop-to-shell handoff (the editor sequence, running the user's shell) instead. |

**Extra modes are yours to undo.** [`try_restore`](https://github.com/ratatui/ratatui/blob/ratatui-v0.30.2/ratatui/src/init.rs) disables raw mode and leaves the alternate screen, nothing else, and the panic hook only calls `restore()`. Mouse capture, bracketed paste, and Kitty keyboard-enhancement flags stay on after a normal exit or a panic unless you disable them. Pop the keyboard flags while still on the alternate screen, because terminals keep separate [keyboard-mode stacks](https://sw.kovidgoyal.net/kitty/keyboard-protocol/) for the main and alternate screens. So disable extras first, then let `restore()` run, including from a hook that wraps Ratatui's:

```rust check=rust/extra-modes
use std::io::stdout;
use std::sync::atomic::{AtomicBool, Ordering};
use ratatui::crossterm::{
    event::{
        DisableBracketedPaste, DisableMouseCapture, EnableBracketedPaste, EnableMouseCapture,
        KeyboardEnhancementFlags, PopKeyboardEnhancementFlags, PushKeyboardEnhancementFlags,
    },
    execute,
    terminal::supports_keyboard_enhancement,
};

static KITTY_PUSHED: AtomicBool = AtomicBool::new(false);

fn enable_extra_modes() -> std::io::Result<()> {
    execute!(stdout(), EnableMouseCapture, EnableBracketedPaste)?;
    if supports_keyboard_enhancement()? {
        execute!(stdout(), PushKeyboardEnhancementFlags(
            KeyboardEnhancementFlags::DISAMBIGUATE_ESCAPE_CODES))?;
        KITTY_PUSHED.store(true, Ordering::Relaxed);
    }
    Ok(())
}

/// Best effort and idempotent: safe from the panic hook and the normal path.
fn disable_extra_modes() {
    if KITTY_PUSHED.swap(false, Ordering::Relaxed) {
        let _ = execute!(stdout(), PopKeyboardEnhancementFlags);
    }
    let _ = execute!(stdout(), DisableBracketedPaste, DisableMouseCapture);
}

fn main() -> color_eyre::Result<()> {
    color_eyre::install()?;
    ratatui::run(|terminal| {
        let ratatui_hook = std::panic::take_hook(); // the hook run() installed
        std::panic::set_hook(Box::new(move |info| {
            disable_extra_modes();                  // still on the alt screen
            ratatui_hook(info);                     // restore(), then the reporting hook
        }));
        let result = enable_extra_modes()
            .map_err(Into::into)
            .and_then(|()| App::default().run(terminal));
        disable_extra_modes();                      // before run() calls restore()
        result
    })
}
```

**Manual setup.** If you construct `Terminal` and configure Crossterm raw/alternate-screen state yourself, you own normal and panic cleanup; wrap the existing reporting hook:

```rust check=rust/panic-hook
color_eyre::install()?;
let report_hook = std::panic::take_hook();
std::panic::set_hook(Box::new(move |info| {
    ratatui::restore();
    report_hook(info);
}));
```

Do not add that `restore()` wrapper on top of `ratatui::run()` or `ratatui::init()`; those managed APIs already install it. A hook that only undoes extra modes and then delegates to the existing hook, as above, is the exception. The fallible helpers are not transactional: `try_init()` can return after an earlier setup step changed terminal state, and `try_restore()` stops at its first teardown error. If the caller requires fallible setup or teardown, handle an error with independent best-effort cleanup attempts (disable raw mode, leave the alternate screen, disable mouse/paste modes, show the cursor) rather than assuming one returned `Err` rolled everything back. `ratatui::restore()` performs the default Crossterm teardown—custom backends must run their matching backend-specific teardown instead. Whichever path you choose, inject setup/teardown failures and verify normal exit, returned errors, and panics in a PTY.

**Child handoff,** following Ratatui's official [external-editor recipe](https://ratatui.rs/recipes/apps/spawn-vim/):

```rust check=rust/editor-handoff
use std::{io::stdout, process::{Command, ExitStatus}};
use ratatui::crossterm::{execute, terminal::{enable_raw_mode, EnterAlternateScreen}};
use color_eyre::eyre::eyre;

fn run_editor(terminal: &mut DefaultTerminal, app: &mut App) -> Result<ExitStatus> {
    app.input.stop();                                    // async apps: cancel the EventStream task
    ratatui::restore();
    let child = Command::new("vim").arg(&app.path).status(); // keep it; no `?` yet
    let reentry = enable_raw_mode()
        .and_then(|()| execute!(stdout(), EnterAlternateScreen))
        .and_then(|()| terminal.clear());                // next draw repaints every cell
    app.input.start();
    app.reload();                                        // the child may have changed state
    match (child, reentry) {
        (Ok(status), Ok(())) => { terminal.draw(|f| app.draw(f))?; Ok(status) }
        (child, reentry) => Err(eyre!("child: {child:?}; reentry: {reentry:?}")),
    }
}
```

Reentry steps are not transactional (see the fallible-helper warning above), and a successful redraw proves only that the renderer recovered. If the app enabled extra modes, call `disable_extra_modes()` before `ratatui::restore()` (otherwise they stay on while the child runs) and `enable_extra_modes()` after reentry; both are defined under *Extra modes* above.

The suspend path is the same sequence with SIGTSTP in place of the child. Bind `KeyCode::Char('z')` with `KeyModifiers::CONTROL` to set a flag, then call this from the loop. Add `signal-hook` for `raise`; Ratatui's `component` template [does the same](https://github.com/ratatui/templates/blob/5903368da4cfce85144f8efc7070f9c175a8f203/component/template/src/tui.rs) for Ctrl+Z:

```rust check=rust/suspend
#[cfg(unix)]
fn suspend(terminal: &mut DefaultTerminal) -> Result<()> {
    disable_extra_modes();
    ratatui::restore();
    signal_hook::low_level::raise(signal_hook::consts::SIGTSTP)?; // returns after `fg` (SIGCONT)
    enable_raw_mode()?;
    execute!(stdout(), EnterAlternateScreen)?;
    enable_extra_modes()?;
    terminal.clear()?;                                            // next draw repaints every cell
    Ok(())
}
```

### Inline viewport

For tools you summon (pickers, prompts, progress), keep the shell visible. `run()` and `init()` always take the alt screen; `ratatui::init_with_options` enables raw mode and the panic hook but not the alt screen, and `Viewport::Inline(n)` reserves `n` rows below the prompt. Draw into `frame.area()`, not `Rect::new(0, 0, ..)`: the viewport starts wherever the cursor was.

- **Permanent lines** (logs, results) go through `Terminal::insert_before(height, draw_fn)`: they push the viewport down, then scroll into scrollback. Enable Ratatui's `scrolling-regions` feature so it does not clear and redraw the viewport.
- **Exit:** the last frame stays on screen with the cursor at the end of its last cell, so later shell output joins that line. To keep the result, `println!()` after `restore()`. To remove a transient UI, `Terminal::clear()` alone is not enough: it restores the old cursor, so return to the viewport origin as below.

```rust check=rust/inline
use ratatui::{backend::Backend, text::Line, widgets::Widget, Terminal, TerminalOptions, Viewport};

fn main() -> std::io::Result<()> {
    let options = TerminalOptions { viewport: Viewport::Inline(3) };
    let mut terminal = ratatui::init_with_options(options); // no alt screen
    let result = run(&mut terminal);
    let _ = erase_inline(&mut terminal); // omit to keep the last frame, then println!()
    ratatui::restore();
    result
}

/// Permanent output above the live UI.
fn log_above<B: Backend>(terminal: &mut Terminal<B>, text: &str) -> Result<(), B::Error> {
    terminal.insert_before(1, |buf| Line::from(text).render(buf.area, buf))
}

/// Erase a transient UI and leave the cursor where it began.
fn erase_inline<B: Backend>(terminal: &mut Terminal<B>) -> Result<(), B::Error> {
    let origin = terminal.get_frame().area().as_position();
    terminal.clear()?;
    terminal.set_cursor_position(origin)
}
```

### Widgets

**Built-in:** `Block` (borders, title, padding; the container for almost everything), `Paragraph` (wrap, alignment, scroll), `List` / `ListState` and `Table` / `TableState` (selectable, virtualized), `Tabs`, `Chart`, `BarChart`, `Gauge` / `LineGauge`, `Sparkline`, `Canvas` (Braille sub-cell drawing for maps and plots), `Scrollbar`, `Calendar`, `Clear`, and `Fill` (one repeated symbol and style, 0.30.1+).

**Custom widgets** implement the `Widget` trait (one-shot) or `StatefulWidget` (with associated state). Both are zero-cost — they're just `(area, buf)` consumers.

**Popups.** Take the rect from `area.centered(horizontal, vertical)` (`Rect::centered`, 0.30.0+; `centered_horizontally` / `centered_vertically` for one axis) and render `Clear` into it before the popup, or the text underneath shows through every cell the popup leaves blank. `Block::shadow` (0.30.1+) paints an offset drop shadow over the cells beside the block, outside the `Clear`ed rect:

```rust check=rust/popup
use ratatui::layout::{Constraint, Offset};
use ratatui::widgets::{Block, Clear, Paragraph, Shadow};
use ratatui::{style::Stylize, Frame};

fn draw_popup(frame: &mut Frame, message: &str) {
    let area = frame.area().centered(Constraint::Percentage(60), Constraint::Length(5));
    frame.render_widget(Clear, area);
    let shadow = Shadow::dark_shade().black().on_dark_gray().offset(Offset::new(2, 1));
    let block = Block::bordered().title("Confirm").shadow(shadow);
    frame.render_widget(Paragraph::new(message).block(block), area);
}
```

**Text-input cursor.** The terminal's real cursor stays hidden unless you call `frame.set_cursor_position((x, y))` during that draw, in screen coordinates (start from `inner.x`, not 0). Call it only while the input has focus: it follows the user's cursor-shape and blink settings, and IME popups and screen readers track it. Compute `x` in cells, not bytes or chars:

```rust check=rust/input-cursor
use ratatui::{buffer::CellWidth, layout::Rect, widgets::{Block, Paragraph}, Frame};

/// `cursor` is a byte offset on a char boundary of `text`.
fn draw_input(frame: &mut Frame, area: Rect, text: &str, cursor: usize) {
    let block = Block::bordered().title("Search");
    let inner = block.inner(area);
    frame.render_widget(Paragraph::new(text).block(block), area);
    let x = (inner.x + text[..cursor].cell_width()).min(inner.right().saturating_sub(1));
    frame.set_cursor_position((x, inner.y));
}
```

**Third-party widgets worth knowing:**
- **`ratatui-textarea`** — multi-line editor with vim/emacs-style bindings. It is the Ratatui org's fork of `tui-textarea` and supports Ratatui 0.30; `tui-textarea` itself is unmaintained and its last release (0.7) requires Ratatui 0.29. Install it from crates.io or `github.com/ratatui/ratatui-textarea`: a malicious GitHub fork with the same name was removed in March 2026.
- **`tui-input`** (single-line input), **`tui-tree-widget`**, **`throbber-widgets-tui`** (spinners), **`tachyonfx`** (shader-like effects, Ratatui org), and **`tui-big-text`**, **`tui-popup`**, **`tui-scrollview`** (maintained in `ratatui/tui-widgets`, also the `tui-widgets` bundle crate).

### Layout

Constraint-based using Cassowary (the same algorithm as iOS Auto Layout):

```rust check=rust/layout
use ratatui::layout::{Layout, Constraint};

let [header, body, status] = Layout::vertical([
    Constraint::Length(3),    // 3 rows for header
    Constraint::Min(0),       // body fills remaining
    Constraint::Length(1),    // 1 row for status
]).areas(frame.area());

let [sidebar, main] = Layout::horizontal([
    Constraint::Percentage(30),
    Constraint::Percentage(70),
]).areas(body);
```

Constraints: `Length(n)` exact, `Min(n)` / `Max(n)` bounds, `Percentage(p)`, `Ratio(num, den)`, and `Fill(weight)` (proportional; prefer over `Percentage` for simple ratios). Ratatui caches split results (`layout-cache`), so re-splitting an area is cheap.

### Styling

```rust check=rust/styling
use ratatui::style::{Color, Modifier, Style, Stylize};

// Direct API
let style = Style::default()
    .fg(Color::Yellow)
    .bg(Color::Black)
    .add_modifier(Modifier::BOLD);

// Stylize extension trait (preferred for brevity)
let span = "Hello".bold().yellow().on_black();
```

**Colors:** 16 ANSI named colors (`Color::Red`, `Color::LightRed`, …), `Color::Indexed(u8)` for 256-color, `Color::Rgb(r, g, b)` for truecolor. `ratatui::crossterm::style::available_color_count()` reads only `COLORTERM`/`TERM`, so use it to gate truecolor or 256-color features, not to honor `NO_COLOR`: Crossterm already drops foreground, background, and underline color codes when `NO_COLOR` is non-empty ([`colored.rs`](https://docs.rs/crossterm/0.29.0/src/crossterm/style/types/colored.rs.html)); `style::force_color_output(true)` overrides it. Bold, reverse, and other attributes are still emitted, so keep state distinguishable without color. Avoid the `SLOW_BLINK`, `RAPID_BLINK`, and `CROSSED_OUT` modifiers; terminals support them poorly.

## Backends: Crossterm vs Termion vs Termwiz

- **Crossterm** — default, cross-platform (Linux/macOS/Windows), pure Rust, MIT. Use this unless you have a specific reason not to.
- **Termion** — Unix-only, older, smaller. Choose only if you want Unix-only and minimal dependencies.
- **Termwiz** — terminal library from the WezTerm project. It can encode Sixel, iTerm2, and kitty images, but Ratatui's termwiz backend doesn't expose them; for images use `ratatui-image`, which works with Crossterm.
- **Termina** — `termina` feature (`TerminaBackend`, Ratatui 0.30.2+), built on the Helix editor's terminal library, which sits between Crossterm and Termwiz and targets newer VT extensions such as the kitty keyboard protocol. Import it as `ratatui::termina` (like `ratatui::crossterm`, not a separate dependency). `ratatui::init()` is Crossterm-only, so set up raw mode and cleanup through Termina yourself. Newer and less proven than Crossterm; choose it only when you need what it exposes.

**Crossterm version conflicts** are a foot-gun: two semver-incompatible Crossterm majors cause separate event queues and broken raw-mode tracking. Run `cargo tree -p crossterm` and verify only one version. Crossterm 0.29 (April 2025) is the current stable; 0.28 is the legacy pin. Ratatui 0.30 has per-version feature flags (`crossterm_0_28`, `crossterm_0_29`) so widget-library authors can pin a Crossterm without forcing it on apps; the default is 0.29, and if both end up enabled `crossterm_0_29` takes precedence. In app code, import Crossterm through the re-export (`use ratatui::crossterm`) rather than a separate dependency, so you get the exact version Ratatui uses.

## State management patterns

**1. Monolithic App struct** (simplest, used in most examples):

```rust check=rust/app-struct
struct App {
    items: Vec<Item>,
    list_state: ListState,
    input: String,
    mode: Mode,
    // ...
}
```

**2. Elm Architecture** (Model + Message + update + view; testable update logic when state is complex):

```rust check=rust/elm
enum Msg { Increment, Decrement, Quit }

fn update(model: &mut Model, msg: Msg) -> Option<Cmd> { todo!() }
fn view(model: &Model, frame: &mut Frame) { /* ... */ }
```

**3. Component pattern** — each component implements an `init`/`handle_events`/`update`/`draw` interface and communicates via `mpsc::UnboundedSender<Action>`. The official `component` template in `ratatui/templates` uses this with Tokio. Best for larger apps; **tui-realm** (crate `tuirealm`) formalizes it as a framework (components, subscriptions, message-based events).

## Async with Tokio

The standard pattern: a cancellable task reads Crossterm's `EventStream` into an `mpsc` channel; the main loop `select!`s over that channel and a tick interval, and draws only after an event or a tick that changed visible state (diffing keeps terminal output minimal, but an unconditional draw still rebuilds the widget tree every tick). `EventStream` needs Crossterm's `event-stream` feature, which Ratatui does not enable: add `crossterm = { version = "0.29", features = ["event-stream"] }` matching Ratatui's Crossterm version so Cargo unifies them, and keep importing through `ratatui::crossterm`.

```rust check=rust/async-input
use std::time::Duration;
use futures::StreamExt;
use ratatui::crossterm::event::{Event, EventStream};
use tokio::{sync::mpsc, task::JoinHandle};
use tokio_util::sync::CancellationToken;

fn spawn_input(tx: mpsc::UnboundedSender<Event>, stop: CancellationToken) -> JoinHandle<()> {
    tokio::spawn(async move {
        let mut events = EventStream::new();
        loop {
            tokio::select! {
                _ = stop.cancelled() => break,
                next = events.next() => match next {
                    Some(Ok(event)) => { let _ = tx.send(event); }
                    _ => break,
                },
            }
        }
    })
}

// Main loop
let (tx, mut rx) = mpsc::unbounded_channel();
let stop = CancellationToken::new();
let input = spawn_input(tx, stop.clone());
let mut tick = tokio::time::interval(Duration::from_millis(250));
let mut dirty = true;
while !app.should_quit {
    if std::mem::take(&mut dirty) {
        terminal.draw(|f| app.draw(f))?;
    }
    tokio::select! {
        event = rx.recv() => match event {
            Some(event) => { app.handle(event); dirty = true; }
            None => break, // reader ended (EOF or error); stop instead of ticking with no input
        },
        _ = tick.tick() => dirty = app.on_tick(), // true only if the tick changed something visible
    }
}
stop.cancel();
input.await?;
```

Cancel and await the reader before `ratatui::restore()` or a child handoff (see [Lifecycle](#lifecycle-and-terminal-handoff)), then spawn a fresh reader with a new token. Sync-only apps need no Tokio: `event::poll(Duration::from_millis(250))`, then `event::read()`.

## Testing

`TestBackend` lets you assert against rendered output:

```rust check=rust/test-backend
use ratatui::{backend::TestBackend, Terminal};

let backend = TestBackend::new(20, 5);
let mut terminal = Terminal::new(backend)?;
terminal.draw(|f| app.draw(f))?;
terminal.backend().assert_buffer_lines([
    "┌Demo──────────────┐",
    "│Counter: 0        │",
    "│                  │",
    "│                  │",
    "└──────────────────┘",
]);
```

Pair with **`insta`** for snapshot testing — `insta::assert_snapshot!(terminal.backend())`, reviewed via `cargo insta review` (the officially documented recipe), with one caveat: **snapshots capture text only — color and style are not asserted.** When color matters (selected-row highlight, error styling), compare `Buffer`s instead: build the expected buffer with `Buffer::with_lines(...)`, apply `set_style` to the regions you care about, and `assert_eq!` against the backend's buffer, as the official counter-app tutorial does.

For the lifecycle layer TestBackend can't reach (event loop, key handling, raw-mode setup and teardown, exit code), the same official recipe now shows a PTY end-to-end test with `termlens`: spawn `env!("CARGO_BIN_EXE_<app>")` at a fixed size, wait for visible text, send keys, and snapshot `terminal.screen()` with insta. Keep it to one or two flows, and pin termlens's version because the crate is new (2026).

**Test at multiple sizes.** Resize bugs live at the edges, so render at 80×24, 60 columns, and your declared hard minimum, snapshotting each under a size-suffixed name (`app_60x24`). A pure `fn compute_layout(area: Rect) -> ...` makes per-size assertions cheap, with no terminal at all.

**Restructuring an event loop so tests can drive it** can regress startup (gitui's first insta + TestBackend attempt was reverted when the refactor dropped the initial notify event and the app opened blank for one tick), so cover first draw in the same tests.

## Debugging

`println!` and `dbg!` are broken inside a running TUI: raw mode stops newline processing (crossterm's docs: "`println!` can't be used, use `write!` instead") and the next draw stomps anything printed, or the alt screen hides it. The working options:

- **Log to a file and tail it** (official recipe): `tracing` + `tracing-subscriber` (env-filter) writing to a plain file with ANSI disabled, then `tail -f app.log` in a second terminal.
- **In-app debug pane** (official recipe): keep `show_debug: bool` in app state, split off a column when toggled, and render `format!("{state:#?}")` into it.
- **tui-logger** (0.18.x, actively maintained) — the ready-made in-app log widget, built on `log`, with `slog` and `tracing` support behind feature flags; the official debug recipe points to it. Its `crossterm` / `termion` features gate only the crate's demo example, not the widget (it takes `ratatui` without default features, so the widget uses your app's backend); translate your own key events into `TuiWidgetEvent`s.
- **Debuggers:** attach from a *second* terminal (`lldb -p <pid>` / `gdb -p`) or use an IDE debugger so the debug console is separate from the app's terminal — stopping the process in its own terminal leaves you at a prompt that's still in raw mode + alt screen.

**Profiling:** use `cargo flamegraph` or `samply`. In raw mode Ctrl+C is a key event, not SIGINT, so it won't end a recording: quit through your app's own key, or attach with `flamegraph --pid <pid>`. In Tokio apps, `tokio-console` shows per-task poll and busy time. The usual slow path is O(n) work inside the render closure (collecting a large `Vec`, recomputing string widths every draw), not widget construction, which Ratatui expects every frame.

## Companion crates

- **clap** — argument parsing. Derive API:
  ```rust check=rust/clap-derive
  use clap::{Parser, Subcommand};

  #[derive(Parser)]
  struct Cli {
      #[arg(short, long)]
      verbose: bool,

      #[command(subcommand)]
      command: Commands,
  }

  #[derive(Subcommand)]
  enum Commands {
      /// List items
      List,
  }
  ```
  Shell completions come from the companion `clap_complete` crate.

- **color-eyre** — rich panic and error reports with span traces; install it before `ratatui::init()` or `run()` so Ratatui wraps its hook.
- **owo-colors** — zero-allocation color formatting. Direct styling emits color; opt into its `supports-colors` feature and use `if_supports_color`, or add your own policy, when output must account for TTY capability and `NO_COLOR`. Recommended over `colored` (older, allocates) and `ansi_term` (unmaintained).

## Alternatives to Ratatui

**Cursive** (`cursive`) — callback-driven, retained-mode, ncurses-like. Widget-rich (Dialog, EditView, SelectView, TextArea, LinearLayout, StackView), best for form-heavy apps with dialogs and menus. The `cursive` crate has had no release since 0.21.1 (August 2024) even though its repo is active, and it depends on crossterm 0.28, so mixing it with Ratatui-ecosystem crates puts two crossterm versions in one build.

```rust check=rust/cursive
use cursive::views::TextView;

let mut siv = cursive::default(); // a runnable Cursive on the default backend
siv.add_layer(TextView::new("Hello, world!"));
siv.add_global_callback('q', |s| s.quit());
siv.run();
```

**iocraft** — declarative React-like with hooks and JSX-style macros, on **taffy** flexbox; choose it if you are coming from React/Ink. **Ratzilla** (`ratatui/ratzilla`) runs Ratatui apps in the browser via WASM, handy for demos. **Dioxus TUI / Plasmo** and the original **`tui-rs`** are unmaintained or archived; don't start new work on them.

## Pitfalls

1. **Naive redraw loop.** Don't busy-loop on `draw`; use `event::poll(timeout)` (sync) or `tokio::select!` (async).
2. **On Windows, both Press and Release events fire.** Filter with `key.kind == KeyEventKind::Press`.
3. **Stateful widgets need state ownership.** `List`, `Table`, `Scrollbar` are `StatefulWidget`s — you pass `&mut ListState` / `TableState` / `ScrollbarState` at render time; the state lives in your App struct, not the widget.
4. **Mouse capture disables terminal text selection.** Most emulators bypass with Shift; document this.
5. **`String::len()` is bytes, not cells.** Use `Line::width()` / `Span::width()` for Ratatui text, but for cursor math or any width that must match what Ratatui draws use `ratatui::buffer::CellWidth` (`s.cell_width()`, 0.30.1+). `Line::width()` and `unicode_width` count halfwidth katakana marks (U+FF9E, U+FF9F) as zero cells; the renderer draws one.
6. **No accessibility layer.** Ratatui has no screen-reader support; [ratatui#2610](https://github.com/ratatui/ratatui/issues/2610) tracks it, and the experimental `tui-a11y` crate is Linux-only. Give screen-reader users a linear mode; see `visual-patterns.md` → *Accessibility*.

## Notable Rust TUI apps to study

**gitui** (Ratatui's flagship demo), **bottom** (widget dashboard), **yazi** (miller columns, image preview), **atuin** (fzf pattern + sync backend), **tokio-console** (async debugger), **helix** (modal editor, custom renderer). Ratatui's own `examples/` directory is also gold; point the user at the closest repo.

## CLI design in Rust

For non-TUI CLIs: **clap** (arguments), **indicatif** (progress bars and spinners; auto-hides on non-TTY), **owo-colors** (zero-allocation colors, recommended; see Companion crates for `NO_COLOR` gating), **anyhow** or **color-eyre** (errors), **env_logger** or **tracing** + **tracing-subscriber** (logging), and **inquire** (modern) or **dialoguer** (stable) for prompts, **cliclack** for Clack-style wizards.

Pair with the principles in `references/cli-basics.md` for argument design, exit codes, and stream handling.
