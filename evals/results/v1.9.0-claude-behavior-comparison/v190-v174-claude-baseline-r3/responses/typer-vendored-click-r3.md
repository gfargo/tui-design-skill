Your working directory doesn't have a Typer app in it, so this is the general wiring. Adapt the names to your project.

## Option 1: Trogon's built-in Typer helper (simplest)

Recent Trogon versions include a Typer integration:

```bash
pip install trogon        # or: uv add trogon
```

```python
# main.py
import typer
from trogon.typer import init_tui

app = typer.Typer()
init_tui(app)  # adds a `tui` command to the app

@app.command()
def greet(name: str, count: int = 1, loud: bool = False):
    """Greet someone."""
    for _ in range(count):
        msg = f"Hello {name}"
        typer.echo(msg.upper() if loud else msg)

@app.command()
def farewell(name: str):
    """Say goodbye."""
    typer.echo(f"Bye {name}")

if __name__ == "__main__":
    app()
```

```bash
python main.py tui
```

`init_tui` accepts `name=` (the app title shown in the TUI) and `command_name=` (if you want something other than `tui`). If `from trogon.typer import ...` fails, your Trogon version is too old. Upgrade it or use Option 2.

## Option 2: Manual wiring (works with any version, and with other Click plug-ins)

Typer apps are Click apps underneath. `typer.main.get_group()` gives you the underlying `click.Group`, which you can pass to any Click tool:

```python
import click
import typer
from trogon import Trogon

app = typer.Typer()

# ... your @app.command()s ...

@app.command()
def tui(ctx: typer.Context):
    """Open an interactive TUI for this CLI."""
    Trogon(
        typer.main.get_group(app),
        app_name="mycli",
        click_context=ctx,
    ).run()
```

The same pattern works for other Click plug-ins: build the Click object with `typer.main.get_group(app)` (or `typer.main.get_command(app)`), then hand it to the plug-in, add it as a command, or wrap it. For example:

```python
click_app = typer.main.get_command(app)
# e.g. some_click_plugin.decorate(click_app), or click_app.add_command(...)
```

If you do this, point your entry point at the modified Click object, not at `app`. Otherwise the plug-in's changes won't be used:

```toml
[project.scripts]
mycli = "mycli.main:click_app"
```

## Gotchas

- **Single-command apps:** A Typer app with only one `@app.command()` collapses into a plain `click.Command`, and Trogon needs a group. Add an `@app.callback()` (even an empty one) to force group mode, or use a second command such as `tui`.
- **Hide the `tui` command from the TUI itself** with `@app.command(hidden=True)` if you don't want it listed. Note that `init_tui` registers its own command.
- **Types:** Trogon builds its form widgets from Click parameter types. Typer maps standard types (`int`, `bool`, `Enum` → choice, `Path`, lists) to Click types, so those all render well. Custom parser callbacks show up as plain text inputs.
- **Help text:** Docstrings and `typer.Option(help=...)` / `typer.Argument(help=...)` appear in the TUI, so filling them in makes the TUI much more useful.

If you share your app's layout (single file or package, and how the entry point is defined), I can wire it into your code directly.
