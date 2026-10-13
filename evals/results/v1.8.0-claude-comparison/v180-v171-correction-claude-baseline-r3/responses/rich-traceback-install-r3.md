**No, `rich.install()` doesn't exist.** The traceback handler is in the `rich.traceback` submodule:

```python
from rich.traceback import install
import click

install(show_locals=False, suppress=[click])

@click.command()
def main():
    ...

if __name__ == "__main__":
    main()
```

Notes for a Click CLI:

- **Call `install()` early**, before `main()` runs. It replaces `sys.excepthook`.
- **Click handles its own errors first.** `ClickException`, `UsageError` and `Abort` are caught by Click and printed as normal one-line messages. Only uncaught exceptions reach Rich. That's usually the split you want: tidy messages for user mistakes, rich tracebacks for real bugs.
- **`suppress=[click]`** collapses Click's internal frames so the traceback shows your code.
- **Be careful with `show_locals=True`.** Local variables can include tokens, passwords or request bodies. If tracebacks end up in CI logs or bug reports, leave it off or enable it only behind a `--debug` flag.
- **Don't confuse it with `rich.pretty.install()`.** That one pretty-prints values in the REPL and doesn't affect tracebacks.
- **For Rich-styled `--help` output too**, look at [`rich-click`](https://github.com/ewels/rich-click). It's a drop-in `import rich_click as click`.

**Precedent you can point to:**

- **pip** vendors Rich (`pip._vendor.rich`) for its progress bars and some error output. Since pip is on nearly every Python install, this is the strongest example.
- **Typer**, which is built on Click, uses Rich for pretty exceptions and help formatting when Rich is installed. It's the closest match to your setup.
- **Hatch**, the PyPA project manager, uses Rich for its terminal output.
- **Textual** and **rich-cli** come from the same author (Textualize), so they show the library's intended use rather than independent adoption.

Those are the ones I'm confident about. Before citing any other project, check its current dependencies, because projects add and drop Rich over time. For example, `pipdeptree -r -p rich` in an environment shows what depends on Rich, or you can read the project's `pyproject.toml`.
