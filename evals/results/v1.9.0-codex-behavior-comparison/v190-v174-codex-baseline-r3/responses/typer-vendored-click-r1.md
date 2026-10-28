Typer builds Click commands internally. **Convert your Typer app to a Click command, then apply Trogon’s `tui` decorator to that command.**

Install:

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


@app.command()
def greet(name: str, count: int = 1):
    """Greet someone."""
    for _ in range(count):
        typer.echo(f"Hello, {name}!")


# Do this after registering all commands and sub-apps.
cli = tui()(get_command(app))


if __name__ == "__main__":
    cli()
```

Run your commands normally, or launch the generated TUI:

```bash
python -m myapp.cli greet Alice --count 2
python -m myapp.cli tui
```

The callback ensures Typer creates a command **group**, even when you have only one command, so Trogon can add the `tui` subcommand.

For an installed executable, point your entry point at the wrapped command:

```toml
[project.scripts]
myapp = "myapp.cli:cli"
```

Then users can run `myapp tui`.

Two details matter:

- Call the wrapped `cli`, including from packaging entry points. Calling `app()` rebuilds Typer’s command tree without the Trogon wrapper.
- Keep the root callback lightweight: it may run when launching the TUI.

Other Click decorators generally use the same bridge: `plugin_decorator(...)(get_command(app))`. Plugins that specifically require a `click.Group` also need the callback shown above.

[Trogon documentation](https://github.com/Textualize/trogon)