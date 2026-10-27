# Python ecosystem — Textual, Rich, prompt_toolkit

Three tools occupy distinct niches: **Textual** (the modern reactive TUI framework — async-first, CSS-styled, web-deployable), **Rich** (output formatting — the rendering engine inside Textual, excellent standalone), and **prompt_toolkit** (input-focused REPLs and shells — powers IPython, ptpython, mycli/pgcli/litecli). They solve different problems. Pick by what the program *is*, not just by Python familiarity.

**Contents:**
- [Quick recommendation](#quick-recommendation)
- [Textual](#textual-textualizetextual) — [Lifecycle and terminal handoff](#lifecycle-and-terminal-handoff) · [Widgets](#widgets) · [Layout (TCSS)](#layout--tcss) · [Events and messages](#events-and-messages) · [Reactive state](#reactive-state) · [Async and workers](#async-and-workers) · [Modal screens](#modal-screens) · [Testing](#testing--pilot--pytest-textual-snapshot) · [Debugging](#debugging) · [Dev tools](#dev-tools) · [Pitfalls](#pitfalls)
- [Rich](#rich-textualizerich) · [prompt_toolkit](#prompt_toolkit) · [Other libraries](#other-libraries)
- [Argument parsing: argparse vs Click vs Typer](#argument-parsing-argparse-vs-click-vs-typer)

## Quick recommendation

| If the user wants… | Use |
|---|---|
| Full-screen TUI app | **Textual** |
| CLI tool with pretty output (tables, panels, syntax) | **Rich** |
| Interactive REPL or shell-like tool | **prompt_toolkit** |
| One or two prompts inside a CLI | **questionary** (built on prompt_toolkit); InquirerPy is unmaintained |
| Argument parsing with type hints | **Typer** (decorator API; bundles its own copy of Click since 0.26) |

**Python floor and distribution:** target 3.11+ for new tools (3.9 and 3.10 are end of life; current Typer, Click 8.2+, prompt_toolkit 3.0.53 and pytest 9 need 3.10+, cyclopts 5 needs 3.11+; Textual 8.2.8 and Rich 15 still install on 3.9). Ship a package with a `[project.scripts]` entry point; users install it isolated with `uv tool install <pkg>` (or `pipx`) and run it once with `uvx <pkg>`.

---

## Textual (Textualize/textual)

**Architectural model: reactive, async-first, message-passing.** App subclass + Widgets in a DOM-like tree (App → Screen → Widgets) + TCSS for layout/style + reactive attributes for state + Messages/Events for communication, all on asyncio.

**Status:** Textualize the company wound down in mid-2025, and Will McGugan maintains Textual and Rich as open source. Textual shipped five major versions (4.0 through 8.0) since the May 2025 announcement, with 8.x current as of mid-2026 (Textual 8.2.8, Rich 15.0.0); releases have slowed. The majors carried breaking renames (`Static.renderable` → `Static.content` in 6.0, `Select.BLANK` → `Select.NULL` in 8.0), so pin your major and read the changelog when upgrading. Harlequin, Dolphie and Posting 2.x track Textual 8.2 (see `exemplar-apps.md`); Toolong, elia and frogmouth are pinned to pre-1.0 Textual, so use them as design references only.

```python check=python/hello-app
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label

class HelloApp(App):
    CSS = "#greeting { padding: 1 2; }"  # or CSS_PATH = "hello.tcss"; that file must exist
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

### Lifecycle and terminal handoff

| Boundary | Textual 8 contract |
|---|---|
| Normal exit | Call `self.exit(result, return_code=...)`; the run lifecycle shuts the driver down in a `finally` path. `return_code` is application metadata, so call `sys.exit(app.return_code)` after `app.run()` when the process must expose it. |
| SIGTERM | Textual installs no SIGTERM handler. On Unix, have the running event loop call `exit` (recipe below); never restore the terminal from a `signal.signal` handler. SIGKILL cannot be cleaned up. |
| Interactive child | Run an argv-based subprocess inside `with self.suspend():`. Textual pauses input/output, restores the child-facing terminal, and resumes plus refreshes afterward. Reload any data the child could have changed; layout refresh does not reread it. Handle `SuspendNotSupported` with a non-terminal alternative because Textual Web cannot hand a local terminal to a child. |
| Foreground suspend | Bind or invoke `suspend_process`; Textual sends SIGTSTP and resumes application mode on Unix. It is intentionally a no-op on Windows and Textual Web. Subscribe to `app_resume_signal` to reload externally mutable data when needed. |

SIGTERM recipe: the loop runs the callback, so `exit` takes the normal shutdown path and the driver restores the terminal. `add_signal_handler` raises `NotImplementedError` on Windows, so skip it there. 143 is 128 plus SIGTERM.

```python check=python/sigterm
import asyncio
import signal
from textual.app import App

class Service(App):
    def on_mount(self) -> None:
        asyncio.get_running_loop().add_signal_handler(
            signal.SIGTERM, lambda: self.exit(return_code=143))
```

[`App.suspend()`](https://textual.textualize.io/guide/app/#suspend-context-manager) lends the terminal to code inside a context manager; `suspend_process` is Unix job control. Neither is a final-exit substitute.

**Ctrl+C is not quit in Textual.** `ctrl+q` is bound to `quit`; `ctrl+c` is bound to `help_quit`, which only shows a toast naming the key that quits, and `Input` and `TextArea` use it to copy ([`app.py`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/app.py), `BINDINGS` and `action_help_quit`). To keep the "Ctrl+C cancels or quits" contract, rebind it with a priority binding so it fires even while a text field has focus, at the cost of copy there:

```python check=python/ctrl-c-quit
from textual.app import App
from textual.binding import Binding

class QuitOnCtrlC(App):
    BINDINGS = [Binding("ctrl+c", "quit", "Quit", show=False, priority=True)]
```

**Inline mode:** `app.run(inline=True)` (since 0.55) renders below the prompt instead of on the alternate screen. Set its height with CSS on `Screen`, as in `Screen { &:inline { height: 50vh; } }`. Inline mode is not supported on Windows.

### Widgets

- **Input:** `Input`, `MaskedInput`, `TextArea` (multi-line, optional tree-sitter syntax highlighting — the `syntax` extras require Python 3.10+ since Textual 5.0), `Button`, `Switch`, `Checkbox`, `RadioButton`, `RadioSet`, `Select`, `OptionList`.
- **Data and display:** `DataTable` (cell/row/column cursors, sortable, virtualized — handles thousands of rows), `Tree`, `DirectoryTree`, `ListView` + `ListItem`, `Markdown`, `RichLog`, `ProgressBar`, `Sparkline`.

Use `DataTable` for any tabular display. Add columns with `add_columns`, rows with `add_rows`, configure cursor type (`cell`/`row`/`column`/`none`), enable `zebra_stripes`, hook into `on_data_table_row_selected`.

### Layout — TCSS

Layout is CSS:

```css check=python/textual-layout
Screen {
    layout: horizontal;
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
- **`layout`** — `vertical | horizontal | grid`. A `Screen` stacks its children vertically, so side-by-side panes need `layout: horizontal` on the Screen (as above) or a `Horizontal` parent.
- **Containers**: `Vertical`, `Horizontal` and `Grid` expand (`width` and `height: 1fr`); `VerticalGroup`, `HorizontalGroup` and `ItemGrid` are `height: auto`, so use a group for a toolbar or form row that hugs its content. Also `VerticalScroll`, `Center`, `Middle`.
- **Sizing**: cells (`width: 30`), percentages (`width: 50%`), `auto`, fractional units (`width: 1fr`); `overflow-x: auto` adds scrollbars. **Grid**: `grid-size: 3 4`, `grid-columns`, `grid-rows`, `column-span`. **Docking**: `dock: top | right | bottom | left` for sticky edges, as `Header` and `Footer` do.

**Selectors**: type (`Button { ... }` matches subclasses too, e.g. your `MyButton(Button)`, unlike web CSS; use a class selector for exact targeting), id (`#dialog`), class (`.error`), pseudo (`:focus`, `:hover`, `:disabled`, `:dark`, `:light`). Nesting works. **Theme variables** (`$primary`, `$panel`, `$text`, `$accent`, `$error`, etc.) — semantic tokens that change with the active theme.

### Events and messages

Handle events with `on_<widget>_<message>` methods (as in the hello app) or the **`@on` decorator with a CSS selector**, preferred when you have many widgets of one type:
```python check=python/on-decorator
from textual import on

@on(Button.Pressed, "#submit")
def handle_submit(self) -> None:
    ...

@on(Button.Pressed, ".danger")
def handle_danger(self, event: Button.Pressed) -> None:
    ...
```

Messages bubble up the DOM. Call `event.stop()` to halt propagation. The idiom: **"attributes down, messages up"** — parents set state on children via attributes; children notify parents via messages.

### Reactive state

```python check=python/reactive
from textual.reactive import reactive, var
from textual.widget import Widget

class Counter(Widget):
    count: reactive[int] = reactive(0)
    label: reactive[str] = reactive("")
    history: reactive[list[int]] = reactive(list)  # callable default: one list per widget
    cursor = var(0)  # watchers fire, but no repaint

    def watch_count(self, old: int, new: int) -> None:
        # called automatically when count changes; repaint is already automatic
        self.log(f"count {old} -> {new}")

    def validate_count(self, value: int) -> int:
        # called before assignment; can clamp or transform
        return max(0, min(10, value))

    def compute_label(self) -> str:
        # derived, read-only reactive; recomputed when count changes
        return f"Count: {self.count}"

    def render(self) -> str:
        return self.label

    def remember(self) -> None:
        self.history.append(self.count)  # in-place edits are invisible to Textual...
        self.mutate_reactive(Counter.history)  # ...so fire watchers and repaint by hand
```

`compute_<name>` only runs for a declared reactive of that name (`label` here), and that reactive becomes read-only. Don't name one `display` — that's Widget's built-in visibility property. Execution order on assignment: **validate → assign → watch → compute**. Modifiers on `reactive(...)`: `init=False` (no watcher on initial assignment), `always_update=True` (fire even when the value didn't change), `layout=True` (re-layout, not just re-render), `bindings=True` (re-evaluate `BINDINGS`), `recompose=True` (re-run `compose()`; the manual route is `await self.remove_children()` + `await self.mount(...)`).

Textual detects assignment, not mutation: after `append` or `d[k] = v`, call `self.mutate_reactive(Cls.attr)`. Use `var` for state that needs watchers but no repaint or relayout (cursor index, cache). To hide a dependent widget, react in `watch_<name>` and set `widget.display = False` (removes it from layout) or `.visible = False` (hides it without reflowing).

### Async and workers

Handlers can be `async def`. The `@work` decorator turns methods into background workers:

```python check=python/workers
import httpx
from textual import work
from textual.widgets import Static
from textual.worker import Worker, WorkerState, get_current_worker

@work(exclusive=True)
async def fetch_data(self, url: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
    self.query_one("#result", Static).update(response.text)

# For blocking code:
@work(thread=True)
def compute_heavy(self) -> None:
    result = expensive_sync_thing()
    self.app.call_from_thread(self.update_result, result)

@work(thread=True, exclusive=True, group="search", exit_on_error=False)
def search(self, query: str) -> None:
    worker = get_current_worker()
    for page in range(20):
        rows = slow_fetch(query, page)
        if worker.is_cancelled:  # a newer search replaced this one
            return
        self.app.call_from_thread(self.show_rows, rows)

def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
    if event.state is WorkerState.ERROR:
        self.notify(str(event.worker.error), severity="error")
```

`call_from_thread(fn, *args)` is required when modifying UI from a thread (vs an asyncio task). It exists only on `App`, so a Screen or Widget worker calls `self.app.call_from_thread(...)`; `self.call_from_thread` there raises `AttributeError`. `post_message` is also thread-safe. `set_interval(secs, callable)` schedules periodic UI updates without blocking.

**Cancellation:** `exclusive=True` cancels earlier workers in the same `group` on the same widget. An async worker stops at its next `await`; a thread worker cannot be interrupted, since cancelling only flips its state to `CANCELLED`, so poll `get_current_worker().is_cancelled` and return before touching the UI. `exit_on_error=False` keeps a failing worker from quitting the app; handle `ERROR` in `on_worker_state_changed` (sent to the widget that started the worker, not bubbled).

**Streaming LLM output:** don't re-render the whole reply per token. `Markdown.get_stream()` batches fragments when the widget can't keep up (about 20 appends a second), and `anchor()` on the scroll container holds the view on the tail until the user scrolls up. Call `stream.stop()` in `finally` to flush queued text.

```python check=python/markdown-stream
@work(exclusive=True)
async def stream_reply(self, chunks) -> None:
    self.query_one(VerticalScroll).anchor()
    stream = Markdown.get_stream(self.query_one(Markdown))
    try:
        async for chunk in chunks:
            await stream.write(chunk)
    finally:
        await stream.stop()
```

### Modal screens

Push a screen on top for dialogs/modals:

```python check=python/modal
from textual import on, work
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label

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

# In your app: a callback works from any handler, no worker needed
def action_delete(self) -> None:
    self.push_screen(ConfirmDialog(), self.after_confirm)

async def after_confirm(self, confirmed: bool | None) -> None:
    if confirmed:
        await self.do_delete()

# Or wait inline, which only works inside a worker:
@work
async def action_delete_inline(self) -> None:
    if await self.push_screen_wait(ConfirmDialog()):
        await self.do_delete()
```

Results come back via `dismiss(value)`; the callback receives it (`None` for a bare `dismiss()`). `push_screen_wait` returns it inline but needs the `@work` decorator; from a plain handler it raises `NoActiveWorker`.

### Testing — Pilot + pytest-textual-snapshot

Pilot drives the app headlessly from pytest:

```python check=python/pilot-test
import pytest
from textual.widgets import Label

@pytest.mark.asyncio  # or asyncio_mode = "auto"
async def test_button_click():
    app = HelloApp()  # the example app above
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.click("#go")
        await pilot.pause()
        assert app.query_one("#greeting", Label).content == "Button pressed!"
```

For SVG snapshots, call `snap_compare("path/to/app.py", press=["tab", "enter", "a"])` in a test; snapshots live under `__snapshots__/` and failures generate an HTML diff page.

Gotchas worth knowing:

- **Async tests need `pytest-asyncio`.** Its default strict mode fails an unmarked `async def` test ("async def functions are not natively supported"). Set `asyncio_mode = "auto"` under `[tool.pytest.ini_options]`, as Textual's own suite does, or mark each test `@pytest.mark.asyncio`.
- **Pin `pytest>=8.4,<9` for snapshot suites.** pytest-textual-snapshot's last release, 1.1.0 (January 2025), pins `syrupy==4.8.0`, which requires `pytest<9`; pytest-asyncio 1.4 needs pytest 8.4 or later. On pytest 9, pip silently picks 1.0.0, which writes `.raw` snapshots instead of `.svg`.
- **`run_test()` runs headless at `size=(80, 24)` and disables notifications and tooltips by default.** A test asserting on a `notify()` toast will silently see nothing — pass `notifications=True` (and `tooltips=True` if relevant) to `run_test`.
- **There's no `App.messages` capture API.** Assert posted messages via a recorder handler on a test App subclass (an `@on(SomeWidget.Changed)` handler appending events to a list — Textual's own test suite does this), or via the `message_hook` parameter of `run_test`, which sees every message in the app. Messages bubble asynchronously, so always `await pilot.pause()` before asserting.
### Debugging

Textual redirects `sys.stdout` and `sys.stderr` while the app runs, so `print()` is captured and sent to `textual console` instead of the screen. What corrupts the display is a write that bypasses the redirect: `sys.__stdout__`, file descriptor 1 (C extensions, `os.write(1, ...)`), and child processes that inherit the terminal. To see output, `pip install textual-dev` (the `textual` CLI lives in that separate package):

- **`textual console`** receives logs and `print()`/`self.log(...)` output in another terminal; start the app with **`textual run --dev myapp.py`**, which also hot-reloads TCSS on save.
- **`textual keys`** — interactive key inspector; press keys to see exactly what events Textual receives, useful for tracking down "why doesn't my binding fire" bugs.

**Profiling:** neither the dev console nor `textual diagnose` (an environment report) measures performance, and there is no built-in FPS overlay. For a "what's slow" answer, attach `py-spy` to the running process (`py-spy record -o profile.svg --pid <pid>`); it needs no code changes, though attaching usually needs `sudo`, and Python 3.15+ has the stdlib `python -m profiling.sampling attach <pid>`. `py-spy` excludes idle threads by default and Textual's main loop mostly awaits, so pass `--idle` if a run over a quiet window shows almost nothing. Heavy synchronous work inside an `async def` handler with no `await` blocks the whole UI; offload it to `@work(thread=True)`, not just `@work`.

### Dev tools

**`textual serve app.py`** serves the app over HTTP/WebSocket in a browser tab with no code changes, so the same codebase runs in a terminal, over SSH, or in a browser. Prefer `textual serve` (self-hosted; works with Textual 8.2) over **textual-web**, the hosted service, which has had no release since 0.8.0 in August 2024.

**Accessibility:** `textual serve` is not an accessibility path. Its browser client paints the terminal grid with xterm.js on a canvas, with xterm's screen-reader mode off, so a screen reader gets no more than it would in a terminal. Textual itself has no screen-reader support; the roadmap item is still open. For reduced motion, `TEXTUAL_ANIMATIONS=none` (or setting `App.animation_level` to `"none"`) makes built-in animations jump to their end state and the loading indicator static; custom timers and spinners must check `app.animation_level` themselves. Design guidance: `visual-patterns.md` → *Accessibility*.

### Pitfalls

1. **Reactives in `__init__` fire watchers before mount** → `NoMatches` errors when watchers try to query DOM. Init in `on_mount` or use the `self.set_reactive(MyClass.attr, value)` method to bypass validators and watchers.
2. **Don't bypass Textual's stdout capture** (see Debugging). `print()` is safe, but `sys.__stdout__`, fd 1 and inherited child-process output corrupt the screen; run children inside `self.suspend()`.
3. **Inside Textual, use `ProgressBar` widget**, not Rich's `Live`/`Progress` — they fight each other for the screen.
4. **`can_focus = True`** on custom widgets that should receive key events. Without this, key events bypass them.
5. **`DataTable.add_rows()` is not a bulk-insert optimization.** It is a plain loop over `add_row()`, paying the same per-row cost, so switching to it won't speed up a slow bulk insert.

---

## Rich (Textualize/rich)

Immediate-mode output formatting — no input handling, no event loop. The de facto Python library for pretty CLI output; it honors `NO_COLOR`.

```python check=python/rich
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

console = Console()
err = Console(stderr=True)  # diagnostics and progress stay off stdout

# Markup syntax (like BBCode)
err.print("[bold red]error:[/] file not found")

# Tables
table = Table(title="Users")
table.add_column("Name", style="cyan")
table.add_column("Email", style="green")
table.add_row("Alice", "alice@example.com")
console.print(table)

# Panels
console.print(Panel.fit("Hello, world!", title="Greeting", border_style="blue"))

# Progress
for item in track(items, description="Processing...", console=err):
    do_work(item)
```

**`from rich.traceback import install; install()`** replaces the default traceback with a syntax-highlighted one with source context. (There is no `rich.install()`; the sibling `rich.pretty.install()` only pretty-prints REPL results.)

**Use Rich vs Textual:** Rich is for tools that *print and exit*. Textual is for apps the user *lives inside*. Rich + Click/Typer is the standard for modern Python CLI tools; pip vendors Rich for its own output, and Textual, Harlequin, and most new Typer-based tools build on it. (Poetry uses cleo and Sphinx does not depend on Rich.)

---

## prompt_toolkit

**Prompt-style** — single-line input with completion, history, syntax highlighting:

```python check=python/prompt-toolkit
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

cmd_completer = WordCompleter(["help", "list", "quit"])
text = prompt("> ", completer=cmd_completer)
```

**Full-screen Application** — HSplit/VSplit/FloatContainer + UIControl + KeyBindings. Powers IPython, ptpython, all the DBCLI tools (mycli, pgcli, litecli), pyvim, pymux.

For one-off prompts inside CLI tools, use **questionary** (built on prompt_toolkit) — much simpler API:

```python check=python/questionary
import sys
import questionary

answer = questionary.text("What's your name?").ask()
if answer is None:  # .ask() turns Ctrl-C into None
    sys.exit(130)
choice = questionary.select(
    "Pick a color",
    choices=["red", "green", "blue"],
).unsafe_ask()  # raises KeyboardInterrupt instead
```

`.ask()` catches Ctrl-C, prints "Cancelled by user" to stdout, and returns `None`; check for `None` and exit 130. `kbi_msg=""` still prints a blank line, so when stdout carries the result, call `.unsafe_ask()` and catch `KeyboardInterrupt`. prompt_toolkit draws prompts on stdout by default, even when stdout is piped, so when stdout carries the result pass `output=create_output(stdout=sys.stderr)` (from `prompt_toolkit.output`). For a single select without questionary, prompt_toolkit 3.0.52+ has a built-in `choice()`.

---

## Other libraries

- **Urwid** — pre-Textual TUI framework, mature and maintained again (4.2.x as of October 2026). New projects should still use Textual.
- **Blessed** (curses wrapper, via `jinxed` on Windows), stdlib **curses** (Unix-only) and **asciimatics** — avoid for new code unless you need fine control or a zero-dep build.
- **InquirerPy** — Python port of Inquirer.js. Unmaintained (last release 0.3.4, June 2022); prefer questionary.
- **tqdm** — progress bars, max performance, the default for ML/data scripts. `with logging_redirect_tqdm():` routes `logging` output around the bar; it does not capture `print()` — use `tqdm.write()`. **alive-progress** is more polished but slightly slower.

---

## Argument parsing: argparse vs Click vs Typer

**argparse** — stdlib, no dependency. Verbose but capable. Since Python 3.14 it colorizes help and can suggest fixes for mistyped choices and subcommands (`suggest_on_error`, on by default in 3.15).

**Click** — decorator-based, very popular:
```python check=python/click
import click

@click.command()
@click.option("--name", default="world", help="Who to greet")
@click.option("--count", default=1, type=int)
def hello(name: str, count: int) -> None:
    """Say hello."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")
```

**Typer** — type-hint-driven (FastAPI's author):
```python check=python/typer
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

**Recommendation: use Typer for new projects.** Type hints give you free validation, documentation, and shell completion. Since 0.26 (May 2026) Typer vendors Click instead of depending on it, so Click plug-ins and extracting the underlying Click app are no longer supported; use Click directly if you need them. **Cyclopts** (Python 3.11+) is the Click-free alternative with a similar type-hint API.

**Trogon** (last release 0.6.0, October 2024; unmaintained) generates a Textual form UI for a **Click** CLI: `from trogon import tui`, then `@tui()` above your Click group. On Click 8.3+ it pre-fills options that have no default with the literal text `Sentinel.UNSET`, and its Typer integration fails on Typer 0.26+; pin `typer<0.26` or write that CLI in Click.
