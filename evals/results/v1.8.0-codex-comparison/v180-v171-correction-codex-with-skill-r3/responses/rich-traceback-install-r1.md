No—use **`rich.traceback.install()`**, not `rich.install()`:

```python
import click
from rich.console import Console
from rich.traceback import install

@click.command()
def cli():
    """Your command."""
    raise RuntimeError("Example unexpected failure")

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

Point your package’s CLI entry point at `main`. Install the hook before calling the Click command.

- `suppress=[click]` hides source context for Click’s frames, keeping attention on your application.
- `show_locals=False` avoids dumping local variables, which may contain credentials.
- The hook formats **uncaught exceptions**. Click still handles `ClickException`, usage errors, and cancellation normally; those don’t suddenly become tracebacks.

[`rich.pretty.install()`](https://rich.readthedocs.io/en/stable/pretty.html) is a different feature: pretty-printing interactive Python results. The [traceback documentation](https://rich.readthedocs.io/en/stable/traceback.html) covers the hook above.

For team precedent:

| Python CLI | How it ships or uses Rich |
|---|---|
| **pip** | Vendors Rich for terminal output, including progress bars. See its [vendored dependencies](https://github.com/pypa/pip/blob/main/src/pip/_vendor/vendor.txt). |
| **HTTPie** | Uses Rich for terminal UI features such as download progress. See its [repository](https://github.com/httpie/cli). |
| **rich-cli** | A CLI built around Rich for syntax highlighting, Markdown, tables, and other formatted output. See [Textualize/rich-cli](https://github.com/Textualize/rich-cli). |
| **Harlequin** | A Python SQL terminal application built with Textual, whose rendering uses Rich. See [Harlequin](https://github.com/tconbeer/harlequin). |

These establish **Rich adoption**, rather than proving each uses the same traceback hook. Don’t cite Poetry or Sphinx as Rich examples: Poetry uses Cleo, and Sphinx does not depend on Rich.

For expected operational failures, keep Click’s concise error messages; reserve detailed tracebacks for unexpected bugs or a debug mode.