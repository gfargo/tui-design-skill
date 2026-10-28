`width` controls size; it doesn’t choose the layout direction. Containers yielded directly from `App.compose()` are children of the `Screen`, whose default layout is vertical. So your sidebar and main area stack even though their widths would fit side by side.

Wrap them in a `Horizontal`:

```python
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static


class MyApp(App):
    CSS = """
    #body {
        height: 1fr;
    }

    #sidebar {
        width: 30;
    }

    #main {
        width: 1fr;
    }

    #toolbar {
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Static("Sidebar")
            with Vertical(id="main"):
                with Horizontal(id="toolbar"):
                    yield Button("Save")
                    yield Button("Cancel")
                yield Static("Main content")
```

Alternatively, set `Screen { layout: horizontal; }` if **all** its direct children should sit side by side.

The toolbar behavior comes from different default sizing:

| Container | Layout | Default width | Default height |
|---|---|---|---|
| `Horizontal` | Horizontal | `1fr` | `1fr` |
| `HorizontalGroup` | Horizontal | `1fr` | `auto` |

A `Horizontal` expands into the available height, so it can occupy the whole screen. A `HorizontalGroup` sizes its height to its content; one-row content produces a one-row group. The same distinction applies to `Vertical` and `VerticalGroup`.

Use `Horizontal` for a region that should fill available space, and `HorizontalGroup` for a content-sized row. Override `height: auto`, a fixed height, or `height: 1fr` when you need different sizing.