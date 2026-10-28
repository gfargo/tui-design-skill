Short answer: on current Typer, you can't plug Trogon in directly. You have to either pin old versions or move off Typer's Click layer. Here are the options, best first.

## Why it's not a one-liner anymore

- **Typer 0.26+ (May 2026) vendors its own copy of Click** instead of depending on it. Click plug-ins and extracting the underlying Click app are no longer supported. Trogon's Typer integration fails on 0.26+.
- **Trogon itself is unmaintained.** The last release was 0.6.0, in October 2024. On **Click 8.3+**, options with no default get pre-filled with the literal text `Sentinel.UNSET`. A user who doesn't notice will submit that string as the value.

## Option 1: Keep Typer and pin old versions (fastest)

```toml
# pyproject.toml
dependencies = [
  "typer>=0.12,<0.26",
  "click<8.3",        # avoids the Sentinel.UNSET pre-fill bug
  "trogon==0.6.0",
]
```

```python
import typer
from trogon.typer import init_tui

app = typer.Typer()
init_tui(app)   # adds a `tui` subcommand

@app.command()
def hello(name: str = "world", count: int = 1) -> None:
    """Say hello."""
    for _ in range(count):
        typer.echo(f"Hello, {name}!")

if __name__ == "__main__":
    app()
```

Users run `myapp tui`, fill in the form, and Trogon runs the command they built. This works, but it freezes you on an old Typer and an unmaintained dependency. Treat it as a stopgap.

## Option 2: Write the CLI in Click (if the TUI matters long-term)

Plug-ins are Click's territory, so the stable path is plain Click:

```python
import click
from trogon import tui

@tui()               # adds `tui` to the group
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

Pin `click<8.3` here too while Trogon stays unpatched. Otherwise, give every option an explicit default so nothing gets pre-filled with `Sentinel.UNSET`.

## Option 3: Stay on current Typer and build the launcher yourself

If you want the latest Typer, write a small Textual app that knows your commands. Give it a list of commands, a form per command, and a "Run" button that exits the TUI and then runs the command. That's a few hundred lines, but you own it. It also avoids the Trogon bugs and lets you add things a generic generator can't, like validation hints and recent-values history. **Cyclopts** (Python 3.11+) is the Click-free alternative with a similar type-hint API, but it has no Trogon equivalent either.

## Whichever you pick

- **Keep it optional.** The TUI should be an extra subcommand (`myapp tui`), not the default. Plain `myapp hello --name x` has to keep working for scripts and for users who need linear output. Don't launch the TUI when stdin/stdout isn't a TTY.
- **Keep output clean.** The command should run *after* the full-screen UI exits, so its stdout reaches the shell and pipes like a normal run. Trogon already does this. If you build your own launcher (Option 3), do the same: return the argv from `App.run()`, then run it.
- **Help text is the UI.** Trogon builds its labels from your `help=` strings and docstrings. Thin help gives a thin form, so fill in every option's help before wiring this up.

**My recommendation:** use Option 1 if you need it this week, and plan to move to Option 2 or 3. Don't take on Trogon as a long-term dependency.
