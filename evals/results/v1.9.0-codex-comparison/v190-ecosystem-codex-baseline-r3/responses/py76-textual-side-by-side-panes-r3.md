**The parent controls how siblings are arranged; each child controls its own contents.** `Vertical` makes the widgets *inside* it stack vertically. It doesn’t determine where that container sits beside its siblings.

Widgets yielded directly from `App.compose()` go into the default `Screen`, whose layout is vertical. Setting widths doesn’t change that arrangement.

Wrap the two panels in a `Horizontal`:

```python
from textual.app import App, ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical
from textual.widgets import Static


class Example(App):
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
    """

    def compose(self) -> ComposeResult:
        with HorizontalGroup(id="toolbar"):
            yield Static("Toolbar")

        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Static("Sidebar")
            with Vertical(id="main"):
                yield Static("Main")
```

Here, `#body` places the panels side by side. The sidebar takes 30 terminal columns; main takes the remaining width.

Your toolbar behavior comes from **different default heights**:

| Container | Child arrangement | Default height |
|---|---|---|
| `Horizontal` | Horizontal | `1fr` — fills available space |
| `HorizontalGroup` | Horizontal | `auto` — fits its contents |
| `Vertical` | Vertical | `1fr` |
| `VerticalGroup` | Vertical | `auto` |

So a `HorizontalGroup` containing one-row widgets naturally becomes one row tall, while a `Horizontal` expands. Choose the appropriate default or override it:

```css
#toolbar {
    height: auto; /* Fit contents, even with Horizontal */
}
```

For an intentionally fixed toolbar, use `height: 3;` or another suitable row count.

Alternatively, if the screen contains only those two panels, `Screen { layout: horizontal; }` fixes their arrangement directly. A wrapper is more useful when a toolbar or footer should span both panels.