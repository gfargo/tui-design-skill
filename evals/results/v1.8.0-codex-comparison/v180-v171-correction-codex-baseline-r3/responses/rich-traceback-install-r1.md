Almost—the installer is in **`rich.traceback`**, not the top-level `rich` module:

```python
import click
from rich.traceback import install

@click.command()
def cli():
    ...

if __name__ == "__main__":
    install(suppress=[click], show_locals=False)
    cli()
```

Add `rich` to your runtime dependencies. `suppress=[click]` keeps Click frames compact while retaining their locations. Install the hook before invoking your CLI. See [Rich’s traceback documentation](https://rich.readthedocs.io/en/stable/traceback.html).

Two details matter:

- This formats **uncaught exceptions**. Click still handles normal usage errors and `ClickException` with its usual concise messages.
- `show_locals=True` displays local variables, which can expose credentials or other sensitive values; leave it off by default.

Concrete precedents you can point your team at:

| CLI | How it ships Rich |
|---|---|
| [HTTPie](https://github.com/httpie/cli) | Uses Rich for terminal output, including download progress. |
| [Hatch](https://github.com/pypa/hatch) | Uses Rich for terminal output in its Click-based CLI—a particularly relevant precedent. |
| [pip](https://github.com/pypa/pip/tree/main/src/pip/_vendor/rich) | Vendors Rich and uses it for progress rendering. |
| [rich-cli](https://github.com/Textualize/rich-cli) | A Click-based CLI built around Rich’s rendering features. |

These establish precedent for **shipping Rich**, not necessarily for enabling its traceback hook. I couldn’t verify the latest repository revisions from this session.