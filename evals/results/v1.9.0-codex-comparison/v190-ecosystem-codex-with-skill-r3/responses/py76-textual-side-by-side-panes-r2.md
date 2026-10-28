**The parent controls where siblings go; each container controls its own children.** Width alone doesn’t create columns.

Widgets yielded directly from `App.compose()` become children of the default `Screen`, whose layout is vertical. Your two `Vertical`s therefore stack. Their `Vertical` type only determines how widgets *inside each pane* are arranged.

For your existing structure, the smallest fix is:

```css
Screen {
    layout: horizontal;
}

#sidebar {
    width: 30;
}

#main {
    width: 1fr;
}
```

`30` means terminal columns; `1fr` takes the remaining available width.

If you also have a toolbar above both panes, use a horizontal wrapper for just the panes:

```python
from textual.app import App, ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical
from textual.widgets import Label


class Example(App):
    CSS = """
    Screen { layout: vertical; }
    #toolbar { height: auto; }
    #panes { height: 1fr; }
    #sidebar { width: 30; }
    #main { width: 1fr; }
    """

    def compose(self) -> ComposeResult:
        with HorizontalGroup(id="toolbar"):
            yield Label("Toolbar")

        with Horizontal(id="panes"):
            with Vertical(id="sidebar"):
                yield Label("Sidebar")
            with Vertical(id="main"):
                yield Label("Main")


Example().run()
```

The toolbar behavior comes from **different default sizing**, despite both containers arranging children horizontally:

| Container | Default sizing | Typical purpose |
|---|---|---|
| `Horizontal` | Expands in width and height (`1fr`) | Main pane area |
| `HorizontalGroup` | Expands in width, content-height (`height: auto`) | Toolbar or form row |

A `HorizontalGroup` containing one-line content naturally becomes one row; it isn’t capped at one row. A `Horizontal` requests available height, so it can occupy the whole screen. Use a group—or `height: auto`—for a toolbar. Use an expanding container for the workspace. If you require exactly one row, set `height: 1` and ensure the controls fit.

For resizing, keep the main pane usable:

```text
80 columns                  60-column fallback
Toolbar                     Toolbar
Sidebar (30) | Main (50)     Main; sidebar opens on demand
```

Those widths assume no extra spacing. At 80×24, keep the toolbar content-height and let the pane area take the remaining rows. In a 60-column split, hide the sidebar behind a keyboard toggle if the main pane needs more than 30 columns. The example adds no borders or repeated markers; avoid adding nested borders that consume the remaining space.