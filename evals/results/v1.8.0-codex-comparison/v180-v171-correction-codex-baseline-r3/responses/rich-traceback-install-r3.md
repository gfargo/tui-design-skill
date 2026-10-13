Almost: use **`rich.traceback.install()`**, not `rich.install()`.

```python
import click
from rich.traceback import install

@click.command()
def cli():
    ...  # Your command

def main():
    install(suppress=[click], show_locals=False)
    cli()

if __name__ == "__main__":
    main()
```

Point your packaged console entry point at `main`. This installs Rich’s handler for uncaught exceptions. `suppress=[click]` reduces Click frames to filenames and line numbers; your application frames retain code context. [Rich traceback documentation](https://rich.readthedocs.io/en/stable/traceback.html)

Click still handles expected errors such as `ClickException` and invalid arguments itself, so those keep their normal concise messages. Unexpected exceptions get Rich tracebacks. [Click exception handling](https://click.palletsprojects.com/en/stable/exceptions/)

Concrete precedents you can share:

| CLI | Evidence that it ships Rich |
|---|---|
| **pip** | Bundles Rich in its [vendored dependency list](https://github.com/pypa/pip/blob/main/src/pip/_vendor/vendor.txt). |
| **Hatch** | Declares both Click and Rich as [runtime dependencies](https://github.com/pypa/hatch/blob/master/pyproject.toml). |
| **rich-cli** | Its `rich` command declares both Click and Rich as [runtime dependencies](https://github.com/Textualize/rich-cli/blob/main/pyproject.toml). |

These establish Rich adoption; they don’t establish that each enables Rich tracebacks. For precedent specifically for **pretty exceptions**, [Typer documents automatic Rich tracebacks](https://typer.tiangolo.com/tutorial/exceptions/)—a useful framework example for your team.