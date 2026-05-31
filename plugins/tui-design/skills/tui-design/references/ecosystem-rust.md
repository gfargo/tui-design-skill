# Rust ecosystem — Ratatui, crossterm, Cursive, clap

Ratatui dominates Rust TUI development — thousands of crates build on it. Forked from `tui-rs` in February 2023. Notable production users: **gitui, bottom, yazi, atuin, bandwhich, oha, tokio-console, csvlens, gpg-tui, systemctl-tui, tenere, kdash**. Helix uses its own custom renderer but follows similar patterns.

**Current line: 0.30** (in beta through late 2025). 0.30 reorganized Ratatui into a modular workspace of crates (better compile times and API stability) and added `no_std` support, but the main `ratatui` crate still re-exports everything, so most apps import it exactly as before. The version detail that actually bites in practice is the crossterm-compatibility story below.

## Quick recommendation

| If the user wants… | Use |
|---|---|
| Modern TUI in Rust | **Ratatui + Crossterm** |
| Form-heavy app with dialogs/menus | **Cursive** (callback-driven, retained-mode) |
| React-like declarative TUI | **iocraft** (newer, hooks + JSX-style + taffy flexbox) |
| Argparse for CLI | **clap** (derive API) |
| Pretty terminal colors | **owo-colors** (zero-allocation, recommended) |
| Non-TUI progress bars | **indicatif** |
| Interactive prompts (one-shot) | **inquire** (modern) or **dialoguer** (stable) |
| Rich panic/error reports | **color-eyre** |
| Fancy modern wizards (Clack-style) | **cliclack** |

**Default: Ratatui + Crossterm + clap + color-eyre.** Use `ratatui/templates` as a starting point — it includes Tokio integration, panic hooks, and the component pattern.

---

## Ratatui (ratatui/ratatui)

**Architectural model: immediate-mode rendering.** Every frame, the application redraws the entire UI from current state. The library handles diffing between intermediate buffers and emits only changed cells — "a video codec for text."

The mental model is **"UI = f(state)"**. You manage app state, the event loop, and timing yourself. Ratatui handles the rendering math.

**Canonical app structure:**

```rust
use ratatui::{prelude::*, widgets::*};
use color_eyre::Result;

fn main() -> Result<()> {
    color_eyre::install()?;            // panic hook restores terminal first
    let mut terminal = ratatui::init();
    let result = App::default().run(&mut terminal);
    ratatui::restore();
    result
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
                    KeyCode::Char('q') => self.should_quit = true,
                    KeyCode::Char('+') | KeyCode::Right => self.counter += 1,
                    KeyCode::Char('-') | KeyCode::Left => self.counter -= 1,
                    _ => {}
                }
            }
        }
        Ok(())
    }
}
```

`ratatui::init()` enables raw mode, enters the alt screen, and constructs a `Terminal<CrosstermBackend>`. `ratatui::restore()` reverses it. **`color_eyre::install()` first** so panics restore the terminal before printing.

## Widgets

**Built-in:**
- **`Block`** — borders, title, padding. The container for almost everything.
- **`Paragraph`** — text with wrap, alignment, scroll offset.
- **`List`** + **`ListState`** — selectable list with virtualized rendering.
- **`Table`** + **`TableState`** — selectable table, virtualized.
- **`Tabs`** — tab bar.
- **`Chart`** — line/scatter chart with X/Y axes.
- **`BarChart`** — horizontal or vertical bars.
- **`Gauge`** / **`LineGauge`** — progress indicator.
- **`Sparkline`** — compact trend visualization.
- **`Canvas`** — sub-cell drawing using Braille markers; great for maps, plots, custom shapes.
- **`Scrollbar`** — pair with any scrollable widget.
- **`Clear`** — paints over an area; use for popup hole-punching.
- **`Calendar`** — monthly calendar.

**Custom widgets** implement the `Widget` trait (one-shot) or `StatefulWidget` (with associated state). Both are zero-cost — they're just `(area, buf)` consumers.

**Third-party widgets worth knowing:**
- **`tui-textarea`** — multi-line editor with vim/emacs bindings.
- **`tui-input`** — single-line input.
- **`tui-tree-widget`** — hierarchical tree.
- **`tui-big-text`** — banner text.
- **`tui-popup`** — modal popups.
- **`tui-logger`** — in-app log pane.
- **`throbber-widgets-tui`** — spinners.

## Layout

Constraint-based using Cassowary (the same algorithm as iOS Auto Layout):

```rust
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

Constraint variants:
- `Length(n)` — exactly n cells.
- `Min(n)` — at least n cells (grows to fill).
- `Max(n)` — at most n cells.
- `Percentage(p)` — p% of available.
- `Ratio(num, den)` — fraction.
- `Fill(weight)` — proportional to weight (newer, prefer over Percentage when ratios are simple).

Layouts cache by default — split once and reuse the resulting `Rect`s in the same frame.

## Styling

```rust
use ratatui::style::{Color, Modifier, Style, Stylize};

// Direct API
let style = Style::default()
    .fg(Color::Yellow)
    .bg(Color::Black)
    .add_modifier(Modifier::BOLD);

// Stylize extension trait (preferred for brevity)
let span = "Hello".bold().yellow().on_black();
```

**Colors:** 16 ANSI named colors (`Color::Red`, `Color::LightRed`, …), `Color::Indexed(u8)` for 256-color, `Color::Rgb(r, g, b)` for truecolor. Detect terminal capability via `crossterm::style::available_color_count()` if you want to gate features.

**Modifiers:** `BOLD`, `DIM`, `ITALIC`, `UNDERLINED`, `SLOW_BLINK`, `RAPID_BLINK`, `REVERSED`, `HIDDEN`, `CROSSED_OUT`. Avoid blink and crossed-out — poorly supported.

## Backends: Crossterm vs Termion vs Termwiz

- **Crossterm** — default, cross-platform (Linux/macOS/Windows), pure Rust, MIT. Use this unless you have a specific reason not to.
- **Termion** — Unix-only, older, smaller. Choose only if you want Unix-only and minimal dependencies.
- **Termwiz** — cross-platform, advanced features (Sixel, kitty image protocol). Choose if you need terminal graphics protocols. Authored by the WezTerm developer.

**Crossterm version conflicts** are a foot-gun: pulling two semver-incompatible Crossterm majors causes separate event queues and broken raw-mode tracking. Always run `cargo tree -p crossterm` and verify only one version. Ratatui 0.30 exposes per-version feature flags (`crossterm_0_28`, `crossterm_0_29`) so widget-library authors can pin a specific Crossterm without forcing it on downstream apps — pick the one flag matching your Crossterm and don't enable both.

## State management patterns

**1. Monolithic App struct** (simplest, used in most examples):

```rust
struct App {
    items: Vec<Item>,
    list_state: ListState,
    input: String,
    mode: Mode,
    // ...
}
```

**2. Elm Architecture** (Model + Message + update + view):

```rust
enum Msg { Increment, Decrement, Quit }

fn update(model: &mut Model, msg: Msg) -> Option<Cmd> { /* ... */ }
fn view(model: &Model, frame: &mut Frame) { /* ... */ }
```

Useful when state is complex and you want testable update logic.

**3. Component pattern** — each component implements an `init`/`handle_events`/`update`/`draw` interface and communicates via `mpsc::UnboundedSender<Action>`. The official `ratatui/templates` repo uses this with Tokio. Best for larger apps.

## Async with Tokio

The standard pattern: one task reads `crossterm::event::EventStream` into an `mpsc` channel; another task emits ticks at fixed intervals; the main loop `select!`s and calls `terminal.draw` on tick or input.

```rust
use tokio::sync::mpsc;
use crossterm::event::{Event, EventStream};
use futures::StreamExt;

let (tx, mut rx) = mpsc::unbounded_channel::<AppEvent>();

// Input task
let input_tx = tx.clone();
tokio::spawn(async move {
    let mut events = EventStream::new();
    while let Some(Ok(event)) = events.next().await {
        let _ = input_tx.send(AppEvent::Crossterm(event));
    }
});

// Tick task
let tick_tx = tx.clone();
tokio::spawn(async move {
    let mut interval = tokio::time::interval(Duration::from_millis(250));
    loop {
        interval.tick().await;
        let _ = tick_tx.send(AppEvent::Tick);
    }
});

// Main loop
loop {
    terminal.draw(|f| app.draw(f))?;
    if let Some(event) = rx.recv().await {
        app.handle(event);
        if app.should_quit { break; }
    }
}
```

For sync-only apps, `event::poll(Duration::from_millis(250))` then `event::read()` works without Tokio.

## Testing

`TestBackend` lets you assert against rendered output:

```rust
use ratatui::{backend::TestBackend, Terminal};

let backend = TestBackend::new(20, 5);
let mut terminal = Terminal::new(backend)?;
terminal.draw(|f| app.draw(f))?;
terminal.backend().assert_buffer_lines([
    "┌─ Demo ───────────┐",
    "│Counter: 0        │",
    "└──────────────────┘",
    "                    ",
    "                    ",
]);
```

Pair with **`insta`** for snapshot testing — `insta::assert_snapshot!(terminal.backend())`. Snapshots are stored as text files and reviewed via `cargo insta review`.

## Companion crates

- **clap** — argument parsing. Derive API:
  ```rust
  #[derive(Parser)]
  struct Cli {
      #[arg(short, long)]
      verbose: bool,

      #[command(subcommand)]
      command: Commands,
  }
  ```
  Best-in-class argparse with auto-generated help, shell completions, and validation.

- **color-eyre** — installs a panic hook that prints rich error reports with source spans. Critical pairing for Ratatui — your panic handler should restore terminal state *first*, then color-eyre prints the report.

- **owo-colors** — zero-allocation color formatting. Recommended over `colored` (older, allocates) and `ansi_term` (unmaintained).

- **indicatif** — progress bars for non-TUI CLIs. Auto-hides on non-TTY.

- **inquire** — modern interactive prompts (text, select, multi-select, confirm). The Rust answer to Inquirer.js.

- **dialoguer** — older, stable alternative to inquire.

- **cliclack** — port of the JS Clack library; modern wizard-style prompts with Unicode connectors.

- **ratatui-image** — image display in Ratatui apps via Sixel/kitty/iTerm2 protocols.

## Panic safety — the critical pattern

A Ratatui app that panics without restoring the terminal leaves the user in raw mode + alt screen + no cursor. Awful. The fix:

```rust
fn install_hooks() -> Result<()> {
    let panic_hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        let _ = ratatui::restore();   // restore FIRST
        panic_hook(info);              // then print panic message
    }));

    color_eyre::install()?;
    Ok(())
}
```

Call `install_hooks()` before `ratatui::init()`. The official templates do this. **This is non-negotiable for production apps.**

## Alternatives to Ratatui

**Cursive** (`cursive`) — callback-driven, retained-mode, ncurses-like. Widget-rich (Dialog, EditView, SelectView, TextArea, LinearLayout, StackView, etc.). Best for form-heavy apps with dialogs and menus where you want a higher-level API. Less popular than Ratatui but stable and well-documented.

```rust
use cursive::{Cursive, views::TextView};

let mut siv = Cursive::default();
siv.add_layer(TextView::new("Hello, world!"));
siv.add_global_callback('q', |s| s.quit());
siv.run();
```

**iocraft** — newer, declarative React-like with hooks and JSX-style macros. Uses **taffy** (the same flexbox engine used by Bevy and Servo). Choose if you want a modern declarative API or are coming from React/Ink.

**Dioxus TUI / Plasmo** — experimental React-like with Dioxus's renderer. Niche; not production-ready.

**Original `tui-rs`** — the predecessor to Ratatui, archived. Migrate to Ratatui.

## Pitfalls

1. **Panic without terminal restore.** Use the panic hook pattern above.
2. **Crossterm version skew.** Run `cargo tree -p crossterm`; ensure one version.
3. **Naive redraw loop.** Don't busy-loop calling `draw`. Use `event::poll(timeout)` for sync, `tokio::select!` for async.
4. **On Windows, both Press and Release events fire.** Filter with `key.kind == KeyEventKind::Press`.
5. **Stateful widgets need state ownership.** `List`, `Table`, `Scrollbar` all use `&mut StatefulWidgetState` — the state lives in your App struct, not the widget.
6. **Mouse capture disables terminal text selection.** Most emulators bypass with Shift; document this.
7. **Layouts cache.** Split once and reuse the `Rect`s; don't re-split mid-frame for the same area.
8. **`String::len()` is bytes, not cells.** Use `unicode_width::UnicodeWidthStr::width(s)` for display width.

---

## Notable Rust TUI apps to study

- **gitui** — git client; Ratatui's flagship demo.
- **bottom** (btm) — system monitor; widget dashboard pattern.
- **yazi** — file manager with image preview; miller columns.
- **atuin** — shell history; fzf pattern + sync backend.
- **csvlens** — CSV viewer.
- **bandwhich** — network monitor.
- **oha** — HTTP load tester.
- **tokio-console** — async runtime debugger; powered by Tokio's tracing.
- **systemctl-tui** — systemd manager.
- **gpg-tui** — GPG key manager.
- **kdash** — Kubernetes TUI.
- **tenere** — chatGPT TUI.
- **helix** — modal editor; custom renderer but Ratatui-adjacent patterns.
- **zellij** — terminal multiplexer.

When the user is building something similar, point them at the relevant repo. Ratatui's own `examples/` directory and the `ratatui/templates` repo are also gold.

---

## CLI design in Rust

For non-TUI CLIs:

- **clap** for argparse.
- **indicatif** for progress bars and spinners (auto-hides on non-TTY).
- **owo-colors** for terminal colors (respects `NO_COLOR` automatically).
- **anyhow** or **color-eyre** for error reporting.
- **env_logger** or **tracing** + **tracing-subscriber** for logging.

Pair with the principles in `references/cli-basics.md` for argument design, exit codes, and stream handling.

---

## Idioms summary

- Always install a panic hook that restores terminal **before** color-eyre runs.
- Use `color_eyre::install()` after the panic hook.
- Filter `KeyEventKind::Press` to avoid double-firing on Windows.
- For async apps, use the EventStream + tick channel + `tokio::select!` pattern.
- Layout once per frame; reuse the `Rect`s.
- Use `Stylize` extension trait for brevity (`.bold().yellow()`).
- For complex apps, copy from `ratatui/templates` rather than starting from scratch.
- Respect `NO_COLOR` — owo-colors and most modern crates do automatically.
- Use `unicode_width` for cell-width math; don't trust `String::len()`.

For deeper patterns shared across apps, see `references/visual-patterns.md` and `references/interaction-patterns.md`.
