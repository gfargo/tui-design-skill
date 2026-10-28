There's no Typer project in the current directory, so here's the general approach. You can paste your app's entry point if you want me to fit it to your code.

## Option 1: Trogon's built-in Typer helper (recommended)

Trogon comes with a helper for Typer apps:

```bash
pip install "trogon[typer]"   # or: uv add "trogon[typer]"
```

```python
# myapp/cli.py
import typer
from trogon.typer import init_tui

app = typer.Typer()
init_tui(app)  # adds a `tui` subcommand

@app.command()
def greet(name: str, shout: bool = False):
    msg = f"Hello {name}"
    typer.echo(msg.upper() if shout else msg)

@app.command()
def version():
    typer.echo("1.0.0")

if __name__ == "__main__":
    app()
```

Now `myapp tui` opens the Textual form UI. To use a different command name, pass it in: `init_tui(app, name="ui")`.

## Option 2: The general pattern for any Click plugin

Under the hood, Typer builds a Click command. Get that object, give it to the plugin, and make your entry point run the Click object instead of `app`:

```python
import typer
from typer.main import get_command
from trogon import tui

app = typer.Typer()

@app.command()
def greet(name: str): ...

@app.command()
def version(): ...

cli = get_command(app)   # a click.Group
cli = tui()(cli)         # apply the Click decorator by hand

if __name__ == "__main__":
    cli()
```

```toml
# pyproject.toml: point the script at `cli`, not `app`
[project.scripts]
myapp = "myapp.cli:cli"
```

Other plugins work the same way. For example, with click-repl it's `register_repl(cli)` and then run `cli()`.

## Things to watch for

- **A single-command Typer app isn't a group.** If you only have one `@app.command()`, Typer collapses it into a plain `click.Command` and there's nothing to attach `tui` to. Fix this by adding an `@app.callback()`, or by setting `typer.Typer(no_args_is_help=True)` together with a callback, so Typer keeps the group.
- **Test it as an installed script.** When you submit the form, Trogon runs your program again using the name it was launched with. It works best through a console-script entry point (`pip install -e .`, then `myapp tui`). Running `python cli.py tui` can behave oddly when Trogon tries to run the command.
- **Help text becomes form labels.** Add `help=` to `typer.Option`/`typer.Argument` and write docstrings on your commands so the TUI's forms are clear. Enum and `Choice` parameters show up as dropdowns.
- **Keep it optional if you like.** To keep Textual out of your core dependencies, wrap the import in `try: from trogon.typer import init_tui` / `except ImportError: pass`, and ship it as an extra (`myapp[tui]`).
