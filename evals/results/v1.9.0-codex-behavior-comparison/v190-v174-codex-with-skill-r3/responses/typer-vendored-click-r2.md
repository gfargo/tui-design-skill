**It depends on your Typer version.** The tui-design skill flags a compatibility break: **Typer 0.26+ vendors Click, so external Click plug-ins such as Trogon are no longer supported.** The old advice to extract a Click command applies to older Typer versions.

Check your version:

```sh
python -c "import typer; print(typer.__version__)"
```

For an existing app on **Typer <0.26**, the legacy wiring looks like this:

```sh
pip install "typer<0.26" "click<8.3" "trogon==0.6.0"
```

```python
import typer
from trogon import tui
from typer.main import get_command

app = typer.Typer()

# Keeps this a command group even with only one command.
@app.callback()
def main():
    """My CLI."""

@app.command()
def greet(name: str, count: int = 1):
    """Greet someone."""
    for _ in range(count):
        typer.echo(f"Hello, {name}!")

# Convert after registering every command and sub-app.
cli = tui()(get_command(app))

if __name__ == "__main__":
    cli()
```

Run either interface:

```sh
python app.py greet Alice --count 2
python app.py tui
```

For an installed command, point the entry point at the **wrapped command**:

```toml
[project.scripts]
myapp = "mypackage.cli:cli"
```

Trogon’s last release was 0.6.0 in 2024. The `click<8.3` constraint avoids its known `Sentinel.UNSET` form-default issue. Treat this as a compatibility option for an existing app.

**For current Typer, I recommend a separate Textual UI** exposed through an explicit `myapp tui` command, with the CLI and TUI calling shared business functions. If automatically generated forms or other Click plug-ins are essential, use Click directly:

```python
import click
from trogon import tui

@tui()
@click.group()
def cli():
    """My CLI."""

@cli.command()
@click.argument("name")
def greet(name):
    click.echo(f"Hello, {name}!")

if __name__ == "__main__":
    cli()
```

Keep TUI launch explicit so ordinary commands continue working in scripts and pipes. Before shipping, smoke-test launch, command execution, exit, and terminal restoration at 80×24 and in a 60-column split.