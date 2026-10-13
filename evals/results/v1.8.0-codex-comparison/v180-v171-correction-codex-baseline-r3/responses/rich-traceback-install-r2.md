**Use `rich.traceback.install()`, not `rich.install()`.** For a Click CLI:

```python
import click
from rich.traceback import install

@click.command()
def cli():
    raise RuntimeError("Something went wrong")

if __name__ == "__main__":
    install(suppress=[click], show_locals=False)
    cli()
```

[`install()`](https://rich.readthedocs.io/en/stable/traceback.html#traceback-handler) registers Rich’s handler for uncaught exceptions. `suppress=[click]` hides the source-code detail for Click’s internal frames while keeping your application frames readable.

Click handles expected errors such as `ClickException` and `UsageError` itself, so those still produce Click’s normal messages. Unexpected exceptions that escape your command get Rich tracebacks. Install the handler in your CLI entry point before invoking the command.

Concrete precedents for **shipping Rich**:

| CLI | How it ships Rich | Source |
|---|---|---|
| **HTTPie** | Declares Rich as a dependency | [Dependency declarations](https://github.com/httpie/cli/blob/master/setup.py) |
| **Hatch** | Declares Rich as a dependency | [Project metadata](https://github.com/pypa/hatch/blob/master/pyproject.toml) |
| **pip** | Vendors Rich inside pip | [Vendored dependencies](https://github.com/pypa/pip/blob/main/src/pip/_vendor/vendor.txt) |

These establish adoption of Rich; they don’t establish that each CLI enables Rich’s global traceback handler. For your team, HTTPie and Hatch demonstrate dependency adoption, while pip demonstrates vendoring.

I couldn’t retrieve live sources in this session, so I haven’t verified the current revisions of those dependency files.