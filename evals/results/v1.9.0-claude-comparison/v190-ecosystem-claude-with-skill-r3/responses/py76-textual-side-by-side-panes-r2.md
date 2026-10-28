Both problems come from the default sizing and layout rules in Textual, not from your `width` rules.

## 1. Sidebar and main stack vertically

`width` sets how wide each child is. It doesn't decide whether children sit side by side. The parent's `layout` decides that, and a `Screen` uses `layout: vertical` by default. Because you yield the two `Vertical`s straight from `App.compose`, their parent is the Screen, so they stack: `#sidebar` 30 cells wide on top, `#main` below it.

You can fix it in either of two ways.

**Option A: make the Screen horizontal (CSS only)**

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

**Option B: wrap the two panes in a `Horizontal`**

```python
from textual.containers import Horizontal, Vertical

def compose(self):
    with Horizontal():
        yield Vertical(id="sidebar")
        yield Vertical(id="main")
```

Option B is usually better once you have a toolbar, because the Screen can stay vertical (toolbar on top, body below) and only the body row is horizontal. A `Header` or `Footer` won't break either option, because they're docked and take no part in the layout.

## 2. `HorizontalGroup` is one row tall, `Horizontal` fills the screen

This is intended behavior. The two containers have different default heights:

| Container | Default `height` | Behavior |
|---|---|---|
| `Horizontal`, `Vertical`, `Grid` | `1fr` | Expands to fill the space left in the parent |
| `HorizontalGroup`, `VerticalGroup`, `ItemGrid` | `auto` | Shrinks to fit its content |

- **`Horizontal` fills the screen** because it's `height: 1fr`. On its own, it takes every row that's left.
- **`HorizontalGroup` is one row** because it's `height: auto`, so it's only as tall as its tallest child. If the children are `Label`s, `Static`s or other one-line widgets, the group is one row. Default `Button`s are 3 rows tall (with their border), so a group of them would be 3 rows.

For a toolbar, use `HorizontalGroup`. For the main body, use `Horizontal`. If you want a taller toolbar, set the height yourself:

```css
#toolbar {
    height: 3;
}
```

You could also put `height: auto` on a `Horizontal` to make it behave like a group.

## Putting it together

```python
from textual.app import App, ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical
from textual.widgets import Button, Footer, Header

class MyApp(App):
    CSS = """
    #toolbar { height: auto; }   /* the default for HorizontalGroup; shown for clarity */
    #body    { height: 1fr; }    /* the default for Horizontal; takes the rest */
    #sidebar { width: 30; border: tall $accent; }
    #main    { width: 1fr; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with HorizontalGroup(id="toolbar"):    # hugs its content
            yield Button("New")
            yield Button("Open")
        with Horizontal(id="body"):            # fills the rest; children go side by side
            yield Vertical(id="sidebar")
            yield Vertical(id="main")
        yield Footer()
```

Here the Screen stays vertical: toolbar, then body. Inside the body, the sidebar is a fixed 30 cells wide and `#main` takes the remaining width.

To check what's happening at runtime, run `textual run --dev app.py` with `textual console` open in another terminal. Or press `ctrl+p` and use the inspector-style commands to see each widget's computed `layout`, `width` and `height`.
