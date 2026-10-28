**Set the horizontal layout on the panes’ parent.** Width controls size; it doesn’t control how siblings are arranged.

Widgets yielded directly from `App.compose()` become children of the default `Screen`, which uses vertical layout. Each `Vertical` controls the arrangement of **its own children**, not its position beside another container.

For your existing two panes, the minimal fix is:

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

Here, `30` means terminal columns, and `1fr` takes the remaining horizontal space.

If you also have a toolbar, use a dedicated `Horizontal` for the panes so the screen can keep stacking toolbar and body vertically:

```python
from textual.app import App, ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical
from textual.widgets import Label

class LayoutApp(App):
    CSS = """
    Screen { layout: vertical; }
    #toolbar { height: auto; }
    #body { height: 1fr; }
    #sidebar { width: 30; }
    #main { width: 1fr; }
    """

    def compose(self) -> ComposeResult:
        with HorizontalGroup(id="toolbar"):
            yield Label("Toolbar")

        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Label("Sidebar")
            with Vertical(id="main"):
                yield Label("Main content")

if __name__ == "__main__":
    LayoutApp().run()
```

The toolbar behavior comes from **different default sizing**:

| Container | Layout | Default sizing |
|---|---|---|
| `Horizontal` | Children side by side | Expands: width and height `1fr` |
| `HorizontalGroup` | Children side by side | Width `1fr`, height `auto` |

A `HorizontalGroup` with one-row content therefore becomes one row tall. Buttons or other taller content can make it taller. A `Horizontal` takes available height, which explains the screen-filling toolbar. Use `HorizontalGroup` for a content-height toolbar, or override a regular `Horizontal` with `height: auto`.

For narrow terminals, plan a sidebar toggle:

```text
80×24:  [toolbar                 ]
        [sidebar: 30][main: ~50  ]

60 cols:[toolbar                 ]
        [main: full width        ]
```

At 60 columns, hide the sidebar and provide a key to open it; the fixed-width version otherwise leaves only about 30 columns for main content. Below your content’s usable minimum, show a “terminal too small” message. The wrapper containers need no added borders or labels.