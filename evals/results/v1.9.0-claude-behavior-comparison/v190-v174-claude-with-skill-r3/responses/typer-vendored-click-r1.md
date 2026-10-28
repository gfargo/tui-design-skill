Short answer: on current Typer you can't wire it up directly. You have to either pin old versions or move off Typer.

## Why it's blocked

- **Since Typer 0.26 (May 2026), Typer bundles its own copy of Click** instead of depending on the real one. As a result, Typer no longer supports Click plug-ins or pulling out the underlying Click app. Trogon's Typer integration fails on 0.26+.
- **Trogon is unmaintained.** Its last release was 0.6.0 in October 2024. It also has a bug on Click 8.3+: options with no default get pre-filled with the literal text `Sentinel.UNSET`.

## Option A: Keep Typer and pin versions (quickest)

```toml
# pyproject.toml
dependencies = [
  "typer>=0.12,<0.26",   # last versions that use real Click
  "click<8.3",           # avoids Trogon's Sentinel.UNSET bug
  "trogon==0.6.0",
]
```

```python
import typer
from trogon.typer import init_tui

app = typer.Typer()
init_tui(app)            # adds a `tui` subcommand

@app.command()
def hello(name: str = "world", count: int = 1) -> None:
    """Say hello."""
    for _ in range(count):
        typer.echo(f"Hello, {name}!")

if __name__ == "__main__":
    app()
```

Users then run `mytool tui`. The catch is that you're stuck on old Typer and Click, and an unmaintained dependency won't get fixes. Treat this as a stopgap.

## Option B: Use Click directly (if the TUI matters long-term)

Trogon works natively with Click:

```python
import click
from trogon import tui

@tui()                   # or @tui(command="ui", help="Open the interactive UI")
@click.group()
def cli(): ...

@cli.command()
@click.option("--name", default="world")
@click.option("--count", default=1, type=int)
def hello(name, count):
    """Say hello."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")
```

You still need `click<8.3` until someone fixes Trogon or forks it. Porting is usually mechanical: type-hinted parameters become `@click.option` / `@click.argument`.

## Option C: Build the form yourself with Textual

If you want to stay on current Typer, write a small Textual app behind a `mytool ui` command. It would show one screen per command, with form fields for the options and a Run button. Then it exits Textual and runs the command through the normal code path. It's more work, but you control the result and avoid dead dependencies.

## Whichever you pick

- Make the TUI a separate subcommand (`tui` or `ui`), not the default. Running the plain command must still work in scripts and CI.
- Write good docstrings and `help=` text. Trogon builds its form labels and descriptions from them, so whatever `--help` shows is what users see in the TUI.
- Test the scripted path with `CliRunner` (`typer.testing` or `click.testing`) so the TUI wrapper can't quietly break it.

My recommendation: use **Option A** if you just want it working today. If the TUI is a real feature for your users, use **B** (switch to Click) or **C** (your own Textual form).
