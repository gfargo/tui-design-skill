Typer builds Click commands internally. The key is to **convert your Typer app to a Click command, then apply Trogon’s decorator to that command**.

Install the dependencies:

```bash
pip install typer trogon
```

For example, in `myapp/cli.py`:

```python
import typer
from trogon import tui
from typer.main import get_command

app = typer.Typer()


@app.callback()
def root():
    """My CLI."""
    # Keeps the app as a command group, even with one command.


@app.command()
def greet(name: str, loud: bool = False):
    """Greet someone."""
    message = f"Hello, {name}!"
    typer.echo(message.upper() if loud else message)


# Do this AFTER registering all commands and sub-apps.
cli = tui()(get_command(app))


def main():
    cli()


if __name__ == "__main__":
    main()
```

Users can then run:

```bash
python -m myapp.cli greet Alice --loud
python -m myapp.cli tui
```

For an installed CLI, point your entry point at the wrapper:

```toml
[project.scripts]
myapp = "myapp.cli:main"
```

That gives users `myapp tui`.

Two details matter:

- Launch through `cli()` rather than `app()`: calling `app()` builds another Click command without the Trogon decoration.
- Keep a root callback if your app has only one command. Typer otherwise promotes that command to the root, leaving no group for the added `tui` subcommand.

Other Click plug-ins often use the same conversion step, though their specific API may expect a Click command or group.