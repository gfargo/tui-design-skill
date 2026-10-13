**Not quite: `rich.install()` doesn't exist.** The call you want is:

```python
from rich.traceback import install
install()
```

There's also `rich.pretty.install()`, but it only pretty-prints values in the REPL. It does nothing for tracebacks.

## Using it in a Click CLI

`install()` replaces `sys.excepthook`, and it works with Click. In standalone mode Click handles `ClickException`, `Abort`, and Ctrl+C itself. Any other exception reaches the hook, and Rich draws the traceback.

Users shouldn't see tracebacks by default, though, pretty or not. Turn expected failures into a short error message, and show tracebacks only with `--debug`:

```python
import sys
import click

@click.group()
@click.option("--debug", is_flag=True, envvar="DEBUG", help="Show full tracebacks.")
def cli(debug: bool) -> None:
    if debug:
        from rich.traceback import install
        install(suppress=[click], show_locals=False)
    else:
        def short_hook(exc_type, exc, tb):
            click.echo(f"Error: {exc}  (re-run with --debug for details)", err=True)
            sys.exit(1)
        sys.excepthook = short_hook

@cli.command()
@click.argument("path")
def load(path: str) -> None:
    try:
        open(path).read()
    except FileNotFoundError:
        # Expected failure: rewrite it, don't trace it
        raise click.ClickException(f"{path} not found. Check the path and try again.")
```

Why this setup:
- **`suppress=[click]`** hides Click's internal frames, so the traceback shows your code instead of the decorator plumbing.
- **Keep `show_locals=False`** (the default). With locals on, every frame's variables get printed, which can include tokens, passwords and config values. That's risky once someone pastes the output into a GitHub issue or a CI log.
- **The traceback goes to stderr.** By default `install()` creates a `Console(stderr=True)`, so stdout stays clean for pipes. Rich also honors `NO_COLOR`.
- **Ctrl+C and broken pipes** (piping into `head`) should exit quietly with no traceback. Click's `Abort` covers Ctrl+C. Check that `yourcli … | head -1` doesn't print a trace.

If you also want Rich-styled `--help` output, the `rich-click` package is a drop-in for Click.

## Precedent to show your team

- **pip** vendors a copy of Rich and uses it for its own output, including progress bars. It's the strongest example: Rich ships inside every Python install.
- **Textual**, the main Python TUI framework, uses Rich for rendering. Textual apps such as **Harlequin**, **Toad**, **Posting** (2.x) and **Dolphie** all run on it.
- **Typer**, a Click-style CLI library, uses Rich for formatted help and tracebacks when Rich is installed. If you look at Typer, check its `pretty_exceptions_show_locals` setting, for the same secrets reason as above.
- **Hatch**, the Python project manager, is built on Click and Rich, which makes it the closest match to your stack. That one comes from my own knowledge, not the skill's reference, so check its `pyproject.toml` before you put it in a team doc.

**Don't cite Poetry or Sphinx.** People often list them as Rich users, but Poetry uses `cleo` and Sphinx doesn't depend on Rich. An example that turns out to be wrong will weaken your case.
