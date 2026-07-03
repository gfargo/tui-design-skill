# Python ecosystem — Textual, Rich, prompt_toolkit

Three tools occupy distinct niches: **Textual** (the modern reactive TUI framework — async-first, CSS-styled, web-deployable), **Rich** (output formatting — the rendering engine inside Textual, excellent standalone), and **prompt_toolkit** (input-focused REPLs and shells — powers IPython, ptpython, mycli/pgcli/litecli). They solve different problems. Pick by what the program *is*, not just by Python familiarity.

## Quick recommendation

| If the user wants… | Use |
|---|---|
| Full-screen TUI app | **Textual** |
| CLI tool with pretty output (tables, panels, syntax) | **Rich** |
| Interactive REPL or shell-like tool | **prompt_toolkit** |
| One or two prompts inside a CLI | **questionary** (built on prompt_toolkit) or **InquirerPy** |
| Argparse with type hints | **Typer** (decorator API on Click) |
| Argparse decorator-style (no type hints) | **Click** |
| Simple progress bar | **tqdm** (max performance) or **alive-progress** (polished, redirect-safe) |

**Default for full TUI: Textual.** It's the only modern Python TUI framework and is genuinely well-designed. **Default for fancy CLI output: Rich.**

---

## Textual (Textualize/textual)

**Architectural model: reactive, async-first, message-passing.** Strongly inspired by web frameworks. App subclass + Widgets in a DOM-like tree (App → Screen → Widgets) + TCSS for layout/style + reactive attributes for state + Messages/Events for communication, all on asyncio.

**Status:** Textualize the company wound down in mid-2025; Will McGugan maintains Textual and Rich as open source. If the user asks "isn't Textual dead?" — no. The release cadence says otherwise: four major versions since the announcement, with 8.x current as of mid-2026. Those majors did carry breaking renames (`Static.renderable` → `Static.content` in 6.0, `Select.BLANK` → `Select.NULL` in 8.0), so pin your major and read the changelog when upgrading.

**Canonical structure:**

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label

class HelloApp(App):
    CSS_PATH = "hello.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Hello, world!", id="greeting")
        yield Button("Click me", id="go", variant="success")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.query_one("#greeting", Label).update("Button pressed!")

    def action_toggle_dark(self) -> None:
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"

if __name__ == "__main__":
    HelloApp().run()
```

`compose()` defines the widget tree (called once on mount). `BINDINGS` declares key bindings declaratively — they auto-render in the `Footer` widget. `action_*` methods are invoked by binding actions. `on_*` methods handle events from child widgets.

## Widgets

Textual ships dozens. Categories:

**Display:** `Label`, `Static`, `Digits`, `Pretty`, `Markdown`, `MarkdownViewer`, `RichLog`, `Log`, `Sparkline`, `Rule`, `Placeholder`.

**Input:** `Input`, `MaskedInput`, `TextArea` (multi-line, optional tree-sitter syntax highlighting — the `syntax` extras require Python 3.10+ since Textual 5.0), `Button`, `Switch`, `Checkbox`, `RadioButton`, `RadioSet`, `Select`, `OptionList`.

**Container/structure:** `Header`, `Footer`, `LoadingIndicator`, `ProgressBar`, `TabbedContent`, `TabPane`, `Tabs`, `Collapsible`.

**Data:** `DataTable` (cell/row/column cursors, sortable, virtualized — handles thousands of rows), `Tree`, `DirectoryTree`, `ListView` + `ListItem`.

`DataTable` is excellent — it's what you should use for any tabular display. Add columns with `add_columns`, rows with `add_rows`, configure cursor type (`cell`/`row`/`column`/`none`), enable `zebra_stripes`, hook into `on_data_table_row_selected`.

## Layout — TCSS

Layout is CSS:

```css
Screen {
    layout: vertical;
}

#sidebar {
    width: 30;
    border: tall $accent;
}

#main {
    width: 1fr;
    layout: vertical;
}

DataTable {
    height: 1fr;
}

.error {
    color: $error;
    text-style: bold;
}
```

Concepts:
- **`layout`** — `vertical | horizontal | grid`.
- **Containers**: `Vertical`, `Horizontal`, `Grid`, `VerticalScroll`, `Center`, `Middle`.
- **Sizing**: cells (`width: 30`), percentages (`width: 50%`), `auto`, fractional units (`width: 1fr`).
- **Grid**: `grid-size: 3 4`, `grid-columns`, `grid-rows`, `grid-gutter`, `column-span`, `row-span`.
- **Docking**: `dock: top | right | bottom | left` for sticky edges. Used for `Header` and `Footer`.
- **Overflow**: `overflow-x: auto` adds scrollbars.

**Selectors**: type (`Button { ... }` matches subclasses too — different from web CSS), id (`#dialog`), class (`.error`), pseudo (`:focus`, `:hover`, `:disabled`, `:dark`, `:light`). Nesting works. **Theme variables** (`$primary`, `$panel`, `$text`, `$accent`, `$error`, etc.) — semantic tokens that change with the active theme.

**Live edit reloads instantly** with `textual run --dev`. Edit your `.tcss` in another window and see changes immediately.

## Events and messages

Two ways to handle events:

**1. Name convention:**
```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "submit":
        ...
```

**2. `@on` decorator with CSS selector** (preferred when you have many of the same widget type):
```python
from textual import on

@on(Button.Pressed, "#submit")
def handle_submit(self) -> None:
    ...

@on(Button.Pressed, ".danger")
def handle_danger(self, event: Button.Pressed) -> None:
    ...
```

Messages bubble up the DOM. Call `event.stop()` to halt propagation. The idiom: **"attributes down, messages up"** — parents set state on children via attributes; children notify parents via messages.

## Reactive state

```python
from textual.reactive import reactive

class Counter(Widget):
    count: reactive[int] = reactive(0)

    def watch_count(self, old: int, new: int) -> None:
        # called automatically when count changes
        self.refresh()

    def validate_count(self, value: int) -> int:
        # called before assignment; can clamp or transform
        return max(0, min(10, value))

    def compute_display(self) -> str:
        # derived attribute; auto-updates when count changes
        return f"Count: {self.count}"

    def render(self) -> str:
        return self.display
```

Execution order on assignment: **validate → assign → compute → watch**. Modifiers on `reactive(...)`:
- `init=False` — don't fire watcher on initial assignment.
- `always_update=True` — fire even when value didn't change.
- `layout=True` — trigger a re-layout, not just a re-render.
- `bindings=True` — re-evaluate `BINDINGS` (useful for context-sensitive bindings).
- `recompose=True` — re-run `compose()` (rebuild children).

This is the heart of Textual's "reactive" claim — it's genuinely declarative state-driven UI.

## Async and workers

Handlers can be `async def`. The `@work` decorator turns methods into background workers:

```python
from textual import work

@work(exclusive=True)
async def fetch_data(self, url: str) -> None:
    response = await httpx.get(url)
    self.query_one("#result").update(response.text)

# For blocking code:
@work(thread=True)
def compute_heavy(self) -> None:
    result = expensive_sync_thing()
    self.call_from_thread(self.update_result, result)
```

`call_from_thread(fn, *args)` is required when modifying UI from a thread (vs an asyncio task). `set_interval(secs, callable)` schedules periodic UI updates without blocking.

## Modal screens

Push a screen on top for dialogs/modals:

```python
from textual.screen import ModalScreen

class ConfirmDialog(ModalScreen[bool]):
    def compose(self) -> ComposeResult:
        yield Label("Are you sure?")
        yield Button("Yes", id="yes", variant="error")
        yield Button("No", id="no")

    @on(Button.Pressed, "#yes")
    def confirm(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def cancel(self) -> None:
        self.dismiss(False)

# In your app — must run in a worker:
@work
async def action_delete(self) -> None:
    if await self.push_screen_wait(ConfirmDialog()):
        await self.do_delete()
```

`push_screen_wait` is the await-able way; results come back via `dismiss(value)`. It only works inside a worker — the `@work` decorator is mandatory, so waiting for the screen doesn't block the app. Calling it from a plain handler raises `NoActiveWorker`.

## Testing — Pilot + pytest-textual-snapshot

Textual has the best testing story of any TUI framework:

```python
async def test_button_click():
    app = HelloApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("tab", "enter")
        await pilot.click("#submit")
        await pilot.pause()
        assert app.query_one("#result", Static).content == "Done"
```

For SVG snapshots:
```python
def test_homepage(snap_compare):
    assert snap_compare("path/to/app.py", press=["tab", "enter", "a"])
```

Snapshots stored under `__snapshots__/`. Failures generate an HTML diff page. This is genuinely production-grade testing — in our view still the most complete story of any TUI framework, though Ratatui's `TestBackend` and Bubble Tea's `teatest` have matured.

Gotchas worth knowing:

- **`run_test()` runs headless at `size=(80, 24)` and disables notifications and tooltips by default.** A test asserting on a `notify()` toast will silently see nothing — pass `notifications=True` (and `tooltips=True` if relevant) to `run_test`.
- **There's no `App.messages` capture API.** Assert posted messages via a recorder handler on a test App subclass (an `@on(SomeWidget.Changed)` handler appending events to a list — Textual's own test suite does this), or via the `message_hook` parameter of `run_test`, which sees every message in the app. Messages bubble asynchronously, so always `await pilot.pause()` before asserting.
- **Form validation is testable end-to-end**: give `Input` `validators=[...]` and `validate_on`, drive it with the pilot, then assert on the recorded `Input.Submitted`/`Changed` message's `event.validation_result` (`is_valid`, `failure_descriptions`) — or on `input.is_valid` / the auto-applied `-invalid`/`-valid` CSS classes.

## Dev tools

The `textual` CLI lives in the separate **`textual-dev`** package — `pip install textual-dev`; installing `textual` alone gives you no `textual` command.

- **`textual run --dev`** — hot-reloads TCSS on save, enables devtools.
- **`textual console`** — separate process receives logs and `print()` output. Run in another terminal: `textual console`, then `textual run --dev myapp.py`.
- **`textual serve app.py`** — serves the app over HTTP/WebSocket; runs in a browser tab. Same Python code, no changes.
- **`textual keys`** — interactive key inspector; press keys to see what events Textual receives.

`textual serve` is genuinely unusual: same codebase runs in terminal, over SSH, or in a browser — and it's the best accessibility story in TUI-land, since browsers have real screen reader support. Prefer it (self-hosted, still maintained) over **textual-web**, the company's hosted service, whose future is unclear post-Textualize.

## Notable Textual apps

- **Toad** — Will McGugan's universal terminal UI for agentic coding, with ACP support for Claude Code, Gemini CLI, and others. The flagship Textual app.
- **Posting** — HTTP client (Postman alternative).
- **Harlequin** — SQL IDE.
- **Toolong** — log viewer for multi-GB files.
- **Memray** — Bloomberg's memory profiler.
- **Dolphie** — MySQL/MariaDB monitor.
- **elia** — chat UI for LLMs.
- **frogmouth** — markdown browser.
- **Trogon** — auto-generates a TUI from a Click/Typer CLI.

## Pitfalls

1. **Reactives in `__init__` fire watchers before mount** → `NoMatches` errors when watchers try to query DOM. Init in `on_mount` or use `set_reactive(MyClass.attr, value)` to bypass watchers.
2. **`compose()` runs once.** To rebuild children, use `reactive(..., recompose=True)` or `await self.remove_children()` + `await self.mount(...)`.
3. **Don't `print()` inside Textual.** Corrupts the screen. Use `self.log(...)` and `textual console` to view.
4. **TCSS type selectors match subclasses** (unlike web CSS). `Button { ... }` matches your custom `MyButton(Button)`. Use class selectors (`.my-button`) when you want exact targeting.
5. **Inside Textual, use `ProgressBar` widget**, not Rich's `Live`/`Progress` — they fight each other for the screen.
6. **For periodic updates from sync code**, use `self.call_from_thread`, not direct attribute assignment.
7. **`can_focus = True`** on custom widgets that should receive key events. Without this, key events bypass them.

---

## Rich (Textualize/rich)

Immediate-mode output formatting — no input handling, no event loop. The de facto Python library for pretty CLI output. Used internally by Textual for rendering.

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

console = Console()

# Markup syntax (like BBCode)
console.print("[bold red]Error:[/] file not found")

# Tables
table = Table(title="Users")
table.add_column("Name", style="cyan")
table.add_column("Email", style="green")
table.add_row("Alice", "alice@example.com")
console.print(table)

# Panels
console.print(Panel.fit("Hello, world!", title="Greeting", border_style="blue"))

# Progress
for item in track(items, description="Processing..."):
    do_work(item)
```

**Components:** `Console`, markup (`[bold red]…[/]`), `Table`, `Panel`, `Columns`, `Tree`, `Syntax` (Pygments), `Markdown`, `Progress` (with multiple tasks), `Live` (animated regions), `RichHandler` for colorized logs, `install()` for pretty tracebacks.

**`rich.install()`** replaces the default Python traceback with a much better one — beautiful syntax highlighting and source context. Drop into any script for free upgrade.

**Use Rich vs Textual:** Rich is for tools that *print and exit*. Textual is for apps the user *lives inside*. Rich + Click/Typer is the standard for modern Python CLI tools (Pip, Poetry, Sphinx, etc. all use Rich).

---

## prompt_toolkit

Two modes:

**1. Prompt-style** — single-line input with completion, history, syntax highlighting:

```python
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

cmd_completer = WordCompleter(["help", "list", "quit"])
text = prompt("> ", completer=cmd_completer)
```

**2. Full-screen Application** — HSplit/VSplit/FloatContainer + UIControl + KeyBindings. Powers IPython, ptpython, all the DBCLI tools (mycli, pgcli, litecli), pyvim, pymux.

**When to choose prompt_toolkit:** you're building a REPL/shell where the central interaction is *typing commands*, with completion, history, multi-line editing, syntax highlighting. Textual can do this but prompt_toolkit is more focused.

For one-off prompts inside CLI tools, use **questionary** (built on prompt_toolkit) — much simpler API:

```python
import questionary

answer = questionary.text("What's your name?").ask()
choice = questionary.select(
    "Pick a color",
    choices=["red", "green", "blue"],
).ask()
```

---

## Other libraries

- **Urwid** — pre-Textual TUI framework; mature and actively maintained again (v3.0.x through 2025, v4.0 in 2026) after years of dormancy. New projects should still use Textual.
- **Blessed** — modernized curses wrapper, cross-platform via `jinxed`. For bespoke games/animations where you want fine control. Not recommended as a first choice.
- **curses** — stdlib, Unix-only, lowest level. Avoid for new code unless you have a strict zero-dep requirement.
- **InquirerPy** — Python port of Inquirer.js. Alternative to questionary.
- **tqdm** — battle-tested progress bars, max performance, the default for ML/data scripts. Survives `print()` interleaving with `with logging_redirect_tqdm():`.
- **alive-progress** — animated, polished progress bars; better visual but slightly slower than tqdm.
- **asciimatics** — animations + form-style TUIs. Niche; Textual has taken over its mindshare.

---

## CLI argparse: argparse vs Click vs Typer

**argparse** — stdlib, no dependency. Verbose but capable.

**Click** — decorator-based, very popular:
```python
import click

@click.command()
@click.option("--name", default="world", help="Who to greet")
@click.option("--count", default=1, type=int)
def hello(name: str, count: int) -> None:
    """Say hello."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")
```

**Typer** — built on Click, type-hint-driven (FastAPI's author). The most ergonomic:
```python
import typer

app = typer.Typer()

@app.command()
def hello(name: str = "world", count: int = 1) -> None:
    """Say hello."""
    for _ in range(count):
        typer.echo(f"Hello, {name}!")

if __name__ == "__main__":
    app()
```

**Recommendation: use Typer for new projects.** Type hints give you free validation, documentation, and shell completion.

**Trogon** auto-generates a Textual TUI from any Click or Typer CLI — drop in `from trogon import Trogon` and your CLI gets an interactive form mode for free.

---

## Idioms summary

- **Textual**: "Attributes down, messages up." Use `@on(Message, "#selector")` for many-of-same-type. `can_focus = True` on custom widgets that need keys. CSS classes + `add_class`/`remove_class` for state-driven styling. Don't `print()` — use `self.log()` + `textual console`. Inside Textual, use `ProgressBar`, not Rich's `Progress`.
- **Rich**: Use markup (`[bold red]…[/]`) over manual style API. Use `Console()` once at module level. Call `rich.install()` for pretty tracebacks. Use `track()` for simple loops, `Progress` for complex multi-task work.
- **prompt_toolkit**: Use **questionary** for simple prompts; full prompt_toolkit only for shell-like tools.
- **Typer + Rich + questionary** is the modern Python CLI stack. **Textual** is the modern TUI stack.

For deeper patterns shared across apps, see `references/visual-patterns.md` and `references/interaction-patterns.md`.
