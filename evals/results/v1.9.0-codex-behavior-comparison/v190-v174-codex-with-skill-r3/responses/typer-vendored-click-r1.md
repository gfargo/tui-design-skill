**Check your Typer version first: the integration changed at Typer 0.26.** Per the tui-design skill’s Python guidance, Typer 0.26+ vendors Click, so extracting a Click command and attaching Click plug-ins is no longer supported.

```bash
python -m pip show typer
```

**For Typer 0.26+: keep Typer and add an explicit TUI command.** Build the UI in Textual and have both interfaces call the same application logic:

```python
import typer

app = typer.Typer()

@app.command()
def hello(name: str):
    typer.echo(f"Hello, {name}!")

@app.command()
def tui():
    """Launch the interactive interface."""
    from .ui import MyApp  # Your Textual App subclass
    MyApp().run()

if __name__ == "__main__":
    app()
```

Users run `myapp tui` for the UI and `myapp hello Alice` for ordinary CLI behavior. This requires building the Textual interface; it does not automatically generate forms from Typer commands.

**For an older Typer app: Trogon can wrap the generated Click group.** Treat this as a legacy, pinned integration:

```bash
python -m pip install 'typer<0.26' 'click<8.3' 'trogon==0.6.0'
```

```python
import typer
from trogon import tui
from typer.main import get_command

app = typer.Typer()

@app.callback()
def main():
    """Example CLI."""  # Ensures a group, even with one command.

@app.command()
def hello(name: str, count: int = 1):
    for _ in range(count):
        typer.echo(f"Hello, {name}!")

# Convert only after registering every command.
cli = tui()(get_command(app))

if __name__ == "__main__":
    cli()  # Invoke the wrapped command.
```

Run:

```bash
python cli.py --help
python cli.py tui
python cli.py hello Alice --count 2
```

For an installed package, point the entry point at the **wrapped command**:

```toml
[project.scripts]
myapp = "my_package.cli:cli"
```

Trogon’s last release was 0.6.0 in October 2024 and it is unmaintained. The Click pin avoids a known Click 8.3+ issue that displays `Sentinel.UNSET` in fields without defaults.

If automatic form generation is essential, use **Click directly**, with `@tui()` above `@click.group()`. Other Click plug-ins face the same Typer 0.26 compatibility boundary. Keep launching the TUI explicit so normal commands remain usable in scripts and pipes.