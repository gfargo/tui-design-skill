No. `rich.install()` doesn't exist. The traceback handler lives in the `rich.traceback` submodule:

```python
import click
from rich.traceback import install

install(suppress=[click])  # hide Click's internal frames from the traceback

@click.group()
def cli():
    ...

if __name__ == "__main__":
    cli()
```

**Why it works with Click:** `install()` replaces `sys.excepthook`. Click handles its own `ClickException`, `Abort` and `Exit` and prints those as normal error messages. Any other exception keeps going up and out of `cli()`, and Rich formats it. So call `install()` at import time in your entry-point module, before `cli()` runs.

**Useful options:**
- `suppress=[click]` collapses framework frames so the traceback shows your code.
- `show_locals=True` prints local variables in each frame. Be careful with it: tracebacks get pasted into tickets and CI logs, so this can leak tokens or passwords. Gate it behind a `--debug` flag or an environment variable rather than turning it on by default.
- `width=`, `max_frames=` and `extra_lines=` help when tracebacks get long.
- If you also want Rich-styled `--help` output, the separate `rich-click` package does that as a drop-in (`import rich_click as click`).

**Precedent for your team:** I'm confident about these:
- **pip** has bundled ("vendored") Rich since about 22.0 and uses it for progress bars and some output. It's probably the strongest example, because pip is careful about what it depends on.
- **Typer** is built on Click and depends on Rich for pretty exceptions and formatted help. It's the closest match to your setup.
- **Hatch** and **PDM**, both Python packaging tools, use Rich for their terminal output.
- **Textual** and **rich-cli** are from Rich's own author. They're less convincing as independent precedent.

Check the current `pyproject.toml` of any of these before you cite them, because dependencies change. I haven't checked them for this answer. Also note that Poetry is not an example: it uses Cleo, not Rich.
