**Check your Typer version first.** The tui-design skill flags a compatibility break: **Typer 0.26+ vendors Click, so external Click plug-ins such as Trogon are no longer supported.** Don’t apply `@tui()` directly to a `typer.Typer()` instance.

You have three practical paths.

**1. Keep current Typer: add an explicit `tui` command.**

Build a small Textual app and launch it from Typer:

```python
import typer

app = typer.Typer()

@app.command()
def hello(name: str = "world"):
    typer.echo(f"Hello, {name}!")

@app.command()
def tui():
    """Open the interactive interface."""
    from .interface import MyTuiApp
    MyTuiApp().run()

if __name__ == "__main__":
    app()
```

This requires building the interface yourself. Have both interfaces call shared business functions so validation and behavior stay consistent. Users keep ordinary commands for scripts and opt into the UI with `myapp tui`.

**2. Want Trogon’s automatically generated forms? Use Click directly.**

```bash
python -m pip install 'click<8.3' 'trogon==0.6.0'
```

```python
import click
from trogon import tui

@tui()  # Apply above the Click group decorator.
@click.group()
def cli():
    """My application."""

@cli.command()
@click.option("--name", default="world", help="Who to greet.")
def hello(name):
    click.echo(f"Hello, {name}!")

if __name__ == "__main__":
    cli()
```

Run either interface:

```bash
python app.py hello --name Ada
python app.py tui
```

Trogon inspects the command tree and generates forms for arguments and options. The Click pin avoids a known issue where Click 8.3+ options without defaults appear as `Sentinel.UNSET`. Trogon’s last release was 0.6.0 in 2024, so treat this as a legacy dependency.

**3. Existing Typer below 0.26: adapt the generated Click command.**

For a legacy installation, after registering **all** commands:

```python
from typer.main import get_command
from trogon import tui

# app = typer.Typer(), with commands already registered
cli = tui()(get_command(app))

if __name__ == "__main__":
    cli()  # Invoke the wrapped command.
```

Expose `cli` in your package entry point too:

```toml
[project.scripts]
myapp = "my_package.cli:cli"
```

This approach needs `typer<0.26` and a compatible Click version; test the pinned combination before shipping.

**My recommendation:** keep current Typer and add a dedicated Textual command for a maintained application. Choose Click plus Trogon if automatic form generation is the main requirement. In either case, keep normal CLI execution available without launching a TUI.