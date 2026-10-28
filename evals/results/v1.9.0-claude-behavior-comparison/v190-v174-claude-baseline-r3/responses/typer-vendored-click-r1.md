I didn't find a Typer app in the working directory, so here's the general setup. Change the names to match your project.

## Option 1: Trogon's built-in Typer support (simplest)

Recent Trogon releases (0.5+) include a Typer helper:

```bash
pip install trogon   # or: uv add trogon / poetry add trogon
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
def deploy(env: str = typer.Option("staging", help="Target environment")):
    typer.echo(f"Deploying to {env}")

if __name__ == "__main__":
    app()
```

Now `myapp tui` opens a Textual form built from your commands, arguments and options. Help text, defaults and types all carry over. You can change the subcommand name: `init_tui(app, command="ui", help="Open interactive mode")`.

## Option 2: Convert to Click and use the `@tui()` decorator

This works with any Trogon version and the same approach applies to other Click plugins. Typer builds a Click command underneath, so you can get that object and wrap it:

```python
import click
import typer
from trogon import tui

app = typer.Typer()

@app.command()
def greet(name: str): ...

@app.command()
def deploy(env: str = "staging"): ...

# Turn the Typer app into a Click group, then put the plugin around it
click_app = typer.main.get_command(app)

@tui()
@click.group()
def cli(): ...

for name, cmd in click_app.commands.items():
    cli.add_command(cmd, name)

if __name__ == "__main__":
    cli()
```

Then point your entry point at `cli` instead of `app`:

```toml
[project.scripts]
myapp = "myapp.cli:cli"
```

## Gotchas

- **One-command apps:** if the Typer app has only one command, `get_command` returns a `click.Command`, not a `Group`, and Trogon needs a group to add `tui` to. Either add a `@app.callback()` so Typer always makes a group, or add a second command.
- **Entry point:** with Option 2, users only get the `tui` subcommand if the console script points at the wrapped Click object.
- **Other Click plugins** (`click-repl`, `click-didyoumean`, `click-help-colors`, etc.) work the same way: call `typer.main.get_command(app)` and apply the plugin to the Click object. Some, like `click-repl`'s `register_repl(group)`, can just be called on the converted group.
- **Testing:** run `myapp tui`. Press `Ctrl+R` to run the command you built, or `Ctrl+T` to toggle showing the equivalent command line.

If you tell me where your Typer app is (or paste `cli.py` and your `pyproject.toml`), I can wire it in for you.
