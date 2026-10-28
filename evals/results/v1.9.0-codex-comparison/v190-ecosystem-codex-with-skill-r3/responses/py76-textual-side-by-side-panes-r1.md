**Set the layout on the parent that holds the panes.** Width controls sizing; it doesn’t choose whether siblings form a row or a column.

Widgets yielded directly from `App.compose()` go into the default `Screen`, whose layout is vertical. Your two `Vertical` containers therefore stack. `Vertical` controls the arrangement of its own children.

For just those two panes, the smallest fix is:

```css
Screen {
    layout: horizontal;
}

#sidebar { width: 30; }
#main    { width: 1fr; }
```

If you also have a toolbar, wrap only the panes in a `Horizontal`:

```python
from textual.app import App, ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical
from textual.widgets import Label

class MyApp(App):
    CSS = """
    Screen { layout: vertical; }

    #toolbar { height: auto; }
    #panes   { height: 1fr; }

    #sidebar { width: 30; }
    #main    { width: 1fr; }
    """

    def compose(self) -> ComposeResult:
        with HorizontalGroup(id="toolbar"):
            yield Label("Toolbar")

        with Horizontal(id="panes"):
            with Vertical(id="sidebar"):
                yield Label("Sidebar")
            with Vertical(id="main"):
                yield Label("Main content")
```

The toolbar behavior comes from **different default heights**:

| Container | Child layout | Default sizing |
|---|---|---|
| `Horizontal` | Horizontal | Expands: width and height `1fr` |
| `HorizontalGroup` | Horizontal | Full width, content height (`auto`) |

A `HorizontalGroup` with one-line content being one row tall is expected. Buttons or taller children can make it taller. A `Horizontal` takes the available height because it defaults to `height: 1fr`. For a content-sized toolbar, use the group or explicitly set `height: auto`; use a fixed height when you intentionally want reserved space.

For resizing, a 30-column sidebar leaves roughly 50 columns at 80×24 and only 30 in a 60-column split. At the narrower size, hide the sidebar and provide a keyboard toggle or navigation screen:

```text
80 columns                 60 columns
Toolbar                    Toolbar
Sidebar (30) | Main        Main (sidebar via toggle)
```

Keep the wrapper containers borderless; add a single divider only if the panes need visual separation.