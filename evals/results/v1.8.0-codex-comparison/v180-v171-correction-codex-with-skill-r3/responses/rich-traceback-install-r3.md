Use **`rich.traceback.install()`**, not `rich.install()`:

```python
import click
from rich.console import Console
from rich.traceback import install

@click.command()
def cli():
    raise RuntimeError("Example unexpected failure")

def main():
    install(
        console=Console(stderr=True),
        show_locals=False,
        suppress=[click],
    )
    cli()

if __name__ == "__main__":
    main()
```

Point your package’s console entry point at `main`. This installs a handler for **uncaught exceptions**, keeps diagnostics on stderr, and hides source context for Click frames. `show_locals=False` avoids dumping local variables that may contain credentials.

Click still handles expected errors such as `click.ClickException` and invalid arguments with its normal concise messages. You don’t need `standalone_mode=False` for unexpected exceptions to reach Rich. Also, `rich.pretty.install()` is a different feature: pretty-printing REPL values.

Useful precedent:

| Project | How it ships Rich |
|---|---|
| [pip](https://github.com/pypa/pip/tree/main/src/pip/_vendor/rich) | Vendors Rich for terminal output, including progress displays. |
| [Hatch](https://github.com/pypa/hatch/blob/master/pyproject.toml) | A Click-based CLI with Rich as a dependency for terminal presentation. |
| [HTTPie](https://github.com/httpie/cli/blob/master/setup.py) | Ships Rich as a dependency for terminal UI components. |
| [Typer](https://typer.tiangolo.com/tutorial/exceptions/) | CLI framework with built-in Rich traceback integration. |

These establish Rich adoption; they don’t all imply the same traceback policy. **Hatch is the closest Click precedent; Typer is the clearest traceback precedent.** Don’t cite Poetry or Sphinx as Rich users.

The canonical API reference is [Rich’s traceback documentation](https://rich.readthedocs.io/en/stable/traceback.html). I applied your tui-design skill; live web verification was unavailable, so the linked dependency files are provided for your team to inspect.