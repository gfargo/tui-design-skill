Both problems come from Textual's default CSS. Your `width` rules are fine. What's wrong is the layout direction and the default heights.

## 1. Sidebar and main stack vertically

`width` only sets how wide a widget is. It doesn't control where widgets go. The **parent's `layout`** decides that, and the `Screen` defaults to `layout: vertical`. So when you yield two containers straight from `App.compose`, they stack top to bottom. Each one is still 30 cells / 1fr wide, just on its own row.

**Fix A: wrap them in a horizontal container** (the usual approach):

```python
from textual.containers import Horizontal, Vertical

def compose(self):
    yield Toolbar()            # optional, see below
    with Horizontal(id="body"):
        yield Vertical(id="sidebar")
        yield Vertical(id="main")
```

**Fix B: make the screen itself horizontal** (only works if nothing else needs to sit above or below them):

```css
Screen {
    layout: horizontal;
}
```

## 2. `HorizontalGroup` vs `Horizontal` heights

The two classes have the same layout and different default sizing:

| Container         | `layout`     | `width` | `height` |
|-------------------|--------------|---------|----------|
| `Horizontal`      | horizontal   | `1fr`   | **`1fr`**  (fills the remaining space) |
| `HorizontalGroup` | horizontal   | `1fr`   | **`auto`** (as tall as its tallest child) |

- **`Horizontal` takes over the screen** because `height: 1fr` claims all the leftover vertical space. That's the behavior you want for the body row, not for a toolbar.
- **`HorizontalGroup` shrinks to one row** because `height: auto` sizes it to its children. If those are `Label`/`Static` (1 line), or widgets whose own height is `auto`/`1fr` inside an auto parent, the result is one line.

**Fix:** use `HorizontalGroup` (or `Horizontal`) for the toolbar and give it, or its children, an explicit height. Keep `Horizontal` with `1fr` for the body:

```css
#toolbar {
    height: 3;          /* or: height: auto, with children that have real height, e.g. Buttons (3 rows) */
}

#body {               /* the Horizontal holding sidebar + main */
    height: 1fr;        /* default; fills what's left below the toolbar */
}

#sidebar { width: 30; }
#main    { width: 1fr; }
```

```python
def compose(self):
    with HorizontalGroup(id="toolbar"):
        yield Button("New")
        yield Button("Open")
    with Horizontal(id="body"):
        yield Vertical(id="sidebar")
        yield Vertical(id="main")
```

To summarize: the parent's `layout` sets the direction. `Horizontal` fills the space (`1fr`), and `HorizontalGroup` wraps its content (`auto`). If a container comes out the wrong size, set its `height` explicitly. To see what's actually happening, run `textual run --dev app.py` and use the devtools/inspector to check computed sizes.
