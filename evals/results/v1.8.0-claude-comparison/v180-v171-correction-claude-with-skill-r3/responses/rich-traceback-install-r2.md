No, `rich.install()` doesn't exist, so that line will raise `AttributeError`. The function you want is in `rich.traceback`:

```python
from rich.traceback import install
install()
```

Don't mix it up with `rich.pretty.install()`. That one only pretty-prints values in the REPL and does nothing to tracebacks.

### Setting it up in a Click CLI

Put the install call at module import time, before your Click group runs:

```python
import click
from rich.traceback import install

install(suppress=[click], show_locals=False)

@click.group()
def cli():
    ...
```

- **`suppress=[click]`** collapses Click's internal frames, so the traceback shows your code instead of Click's dispatch machinery.
- **Keep `show_locals=False`** (the default) in anything you ship. Local variables can hold tokens, passwords or request bodies, and those end up in screenshots and bug reports. If you want locals while debugging, turn them on behind an env var or a `--debug` flag.
- **This only covers crashes you didn't expect.** Click still prints `click.ClickException` and `UsageError` as short one-line errors, which is the right behaviour for user mistakes. Keep raising those for expected failures and let Rich handle real bugs.
- **Stream:** Rich prints tracebacks to stderr by default, so stdout stays clean for pipes. If you print other errors or progress with Rich, use a separate `Console(stderr=True)` for them. Rich also respects `NO_COLOR`.

### Precedent you can point your team at

- **pip** vendors Rich and uses it for its own terminal output, so most Python users already see Rich output.
- **Textual** (Textualize's TUI framework) is built on Rich.
- **Harlequin**, the terminal SQL IDE, is built on it too.
- **Typer** pairs with Rich for help text and pretty exceptions, and most new Typer-based CLIs use that combination.

Don't cite **Poetry** (it uses cleo) or **Sphinx** (it doesn't depend on Rich). Both come up often as Rich users, and both are wrong.

If you're starting a new CLI rather than adding to an existing one, consider Typer. It gives you Rich-formatted errors and help with less setup. But Typer 0.26+ bundles its own copy of Click, so if you depend on Click plugins, stay on Click and use the setup above.
