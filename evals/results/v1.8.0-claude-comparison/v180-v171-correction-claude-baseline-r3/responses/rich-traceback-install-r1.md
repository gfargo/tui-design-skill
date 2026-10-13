No, `rich.install()` doesn't exist. The traceback handler lives in `rich.traceback`:

```python
from rich.traceback import install
install(show_locals=False, suppress=[click])
```

## Wiring it into a Click CLI

```python
import click
from rich.traceback import install

install(suppress=[click], show_locals=False)

@click.group()
def cli():
    ...

if __name__ == "__main__":
    cli()
```

Things to know:

- **Call `install()` early**, before anything can raise. Putting it at the top of your entry-point module is enough. It replaces `sys.excepthook`.
- **Click's standalone mode doesn't block it.** Click catches `ClickException` and `Abort` itself and prints a short message. Any other exception reaches `sys.excepthook`, which is where Rich takes over. That's the split you want: user errors stay short, real bugs get the full traceback.
- **`suppress=[click]`** collapses Click's internal frames so the trace shows your code, not `click/core.py` dispatch.
- **Leave `show_locals` off by default.** Locals can contain tokens, passwords and request bodies, and tracebacks end up pasted into tickets and Slack. You could turn it on behind a `--debug` flag or an environment variable:
  ```python
  install(suppress=[click], show_locals=bool(os.environ.get("MYCLI_DEBUG")))
  ```
- **Related tools:**
  - `rich-click` swaps in Rich-formatted `--help` output with one import.
  - If you're open to switching, Typer is built on Click and has Rich tracebacks built in (`pretty_exceptions_enable`, `pretty_exceptions_show_locals`).

## CLIs that ship Rich

These are from memory. I haven't checked them in this session, so confirm against each project's dependencies before citing them in a doc.

- **pip**: vendors Rich (`pip/_vendor/rich`) for progress bars and some error output. This is probably your strongest example, since nearly every Python install has it.
- **Typer**: uses Rich for help output and exception formatting. It's from the FastAPI author.
- **Hatch** (PyPA project manager): uses Rich for its output.
- **PDM**: uses Rich for terminal output.
- **HTTPie**: adopted Rich in the 3.x line, mainly for progress and display.
- **Textual and Textualize's own tools**: same company as Rich, so it supports adoption but is a weaker example.

For your team, pip and Hatch are the best two to cite: both are PyPA tools that put Rich in front of very large numbers of users. To verify quickly, `pip show hatch pdm httpie` lists their `Requires` fields, and `python -c "import pip._vendor.rich"` confirms the copy vendored into pip.
