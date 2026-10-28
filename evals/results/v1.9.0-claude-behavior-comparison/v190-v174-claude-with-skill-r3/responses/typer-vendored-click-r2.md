I checked the skill's Python reference, and there's a catch: **on current Typer (0.26+, May 2026), Click plug-ins like Trogon don't work.** Typer now bundles its own copy of Click instead of using the `click` package, so plug-ins that hook into Click can't attach. Trogon itself has had no release since 0.6.0 (October 2024). On Click 8.3+ it also fills options that have no default with the literal text `Sentinel.UNSET`.

You have three workable options. Which one fits depends on how long you plan to keep the TUI.

## Option 1: Pin old versions and use Trogon's Typer integration (quickest, but a dead end)

```toml
# pyproject.toml
[project]
dependencies = [
    "typer<0.26",   # last versions that use the real click package
    "click<8.3",    # avoids the Sentinel.UNSET pre-fill bug
]

[project.optional-dependencies]
tui = ["trogon==0.6.0"]
```

```python
import typer

app = typer.Typer()

@app.command()
def hello(name: str = "world", count: int = 1) -> None:
    """Say hello."""
    for _ in range(count):
        typer.echo(f"Hello, {name}!")

try:
    from trogon.typer import init_tui
    init_tui(app)          # adds a `tui` subcommand
except ImportError:
    pass                   # TUI is optional; the CLI still works without it

if __name__ == "__main__":
    app()
```

Users run `mytool tui`, fill in the form, and Trogon then runs the command they built. Pin the exact versions, because this setup breaks on any Typer upgrade and you'll stay on old Typer for good. I wrote this from memory of Trogon's API, so check `init_tui`'s signature against the installed 0.6.0 before relying on it.

## Option 2: Write the CLI in Click and use `@tui()` (if you want a generated form long-term)

```python
import click
from trogon import tui

@tui()
@click.group()
def cli() -> None: ...

@cli.command()
@click.option("--name", default="world", help="Who to greet")
@click.option("--count", default=1, type=int)
def hello(name: str, count: int) -> None:
    """Say hello."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")
```

This avoids the Typer conflict, but you still need `click<8.3` and you still depend on an unmaintained package.

## Option 3: Keep current Typer and build a small Textual `tui` command (my recommendation if the TUI matters)

A generated form shows every option the same way. A small hand-built Textual screen can show the 5–8 actions people actually use. Keep the TUI as a front-end that only builds an argument list and then calls the same command functions. That way the CLI stays the single source of truth and scripts never depend on it.

## Whichever you pick

- **Make the TUI optional.** Put it behind an extra (`uv tool install 'mytool[tui]'`) and keep all normal commands working without a terminal, so pipes, CI and screen-reader users aren't affected.
- **Keep stdout clean.** The form should exit and restore the terminal before the command runs, so only the command's real output goes to stdout.
- **Keep testing the CLI directly.** Use `typer.testing.CliRunner` (or Click's) on the commands, and add one smoke test that `mytool tui --help` exists.

If you're not using Typer for anything Click can't do, I'd go with Option 3, or Option 2 if a generated form is enough. Option 1 locks you to old Typer. If you share your app's command structure, I can sketch the Textual screen for it.
