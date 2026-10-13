Use **`rich.traceback.install()`**, not `rich.install()`:

```python
import click
from rich.console import Console
from rich.traceback import install

@click.command()
def cli():
    raise RuntimeError("Something went wrong")

def main():
    install(
        console=Console(stderr=True),
        suppress=[click],
        show_locals=False,
    )
    cli()

if __name__ == "__main__":
    main()
```

Point your package’s console entry point at `main`. Install the hook before invoking Click.

- It formats **uncaught exceptions**. Click still handles expected errors such as `ClickException` and `BadParameter` with its normal concise messages.
- `suppress=[click]` hides source context for Click frames; the frames remain visible.
- `show_locals=False` avoids dumping local variable values.
- `rich.pretty.install()` is a different hook for pretty-printing REPL results.

For your team, these are useful **Rich adoption precedents**, though they don’t all enable pretty tracebacks:

| Python CLI | How it ships Rich | Source |
|---|---|---|
| **pip** | Vendors Rich for terminal output, including progress bars | [Vendored dependencies](https://github.com/pypa/pip/blob/main/src/pip/_vendor/vendor.txt) |
| **Hatch** | Declares Rich as a dependency; a particularly relevant Click-based example | [Package configuration](https://github.com/pypa/hatch/blob/master/pyproject.toml) |
| **Rich CLI** | Uses Rich for terminal rendering of files and data | [Project](https://github.com/Textualize/rich-cli) |
| **Harlequin** | SQL CLI/TUI built on Textual and Rich | [Package configuration](https://github.com/tconbeer/harlequin/blob/main/pyproject.toml) |

The [Rich traceback documentation](https://rich.readthedocs.io/en/stable/traceback.html) covers installation and Click suppression. For a user-facing CLI, keep expected failures concise and reserve detailed tracebacks for debugging.

I applied the requested tui-design skill. Live source retrieval was unavailable, so I couldn’t verify the linked repositories’ current dependency files.