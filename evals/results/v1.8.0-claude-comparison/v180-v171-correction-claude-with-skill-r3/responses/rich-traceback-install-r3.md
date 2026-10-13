No, `rich.install()` doesn't exist. You need `from rich.traceback import install`. There's also `rich.pretty.install()`, but that only pretty-prints values in the REPL and does nothing for tracebacks.

## Wiring it into Click

```python
import click
from rich.traceback import install

install(suppress=[click], show_locals=False)

@click.command()
def main():
    ...
```

- **Install it at module import time, before Click runs.** Click handles its own exceptions (`ClickException`, `Abort`, Ctrl-C) and prints those as normal one-line errors, which is what users should see. Any other uncaught exception goes to `sys.excepthook`, and that's the hook Rich replaces. So user errors stay short and real bugs get the full traceback.
- **`suppress=[click]`** collapses Click's internal stack frames so the traceback starts at your code.
- **Keep `show_locals=False` (the default) in shipped builds.** If you turn on local variables, tokens, passwords and file paths can end up in tracebacks that people paste into issues. Turn it on only behind a `--debug` flag or an environment variable.
- **Keep diagnostics on stderr.** The traceback handler already writes to stderr by default. Do the same for your own errors and progress output with a separate `Console(stderr=True)`, so stdout stays clean for piping. Rich respects `NO_COLOR`.
- If you also want styled `--help` output, the separate `rich-click` package does that. It doesn't change tracebacks.

## Precedent to show your team

- **pip** vendors Rich for its own output, including progress bars and logging. It's the strongest example because nearly every Python developer has run it.
- **Typer** is built on Click and uses Rich for its help output and pretty exceptions. That's close to the setup you're proposing.
- **Textual** uses Rich as its rendering engine, and **Harlequin** (a terminal SQL IDE) is built on Textual.
- Many newer Typer-based CLIs pull in Rich through Typer.

Two projects are often cited as Rich users but aren't: **Poetry** uses `cleo`, and **Sphinx** doesn't depend on Rich. If someone on your team brings them up, that's the correction.

Rich is meant for tools that print output and exit, which is what a Click CLI does. If you later want a full-screen interactive app, that's what Textual is for.
