I didn't open your project, so this is based on what you described and on how Textual's default styles work.

## 1. Why `#sidebar` and `#main` stack

Widgets you yield from `App.compose` become children of the **Screen**, and the Screen uses `layout: vertical` by default. `width: 30` and `width: 1fr` only set how wide each container is. They don't decide where it goes. So you get a 30-column sidebar, and below it a full-width main area.

Use either of these fixes.

**Option A: put them inside a `Horizontal`** (recommended)

```python
from textual.containers import Horizontal, Vertical

def compose(self):
    yield Header()
    with Horizontal(id="body"):
        with Vertical(id="sidebar"):
            ...
        with Vertical(id="main"):
            ...
    yield Footer()
```

**Option B: change the Screen's layout** (only if nothing else needs to stack vertically on the Screen)

```css
Screen { layout: horizontal; }
```

`Header` and `Footer` are docked, so they aren't affected by the Screen's layout. A toolbar that isn't docked would end up in the row next to the sidebar, which is why Option A is usually the better choice.

## 2. Why `HorizontalGroup` is short and `Horizontal` fills the screen

The two containers have different default heights:

| Container | layout | width | height |
|---|---|---|---|
| `Horizontal` | horizontal | `1fr` | **`1fr`** (takes all the remaining space) |
| `HorizontalGroup` | horizontal | `1fr` | **`auto`** (as tall as its children) |
| `Vertical` / `VerticalGroup` | vertical | `1fr` | `1fr` / `auto` |

This is intended: the "Group" variants are for strips like toolbars, and the plain ones are for regions that should fill the space. Your toolbar is one row tall because its children (for example, `Label`s or compact buttons) are one row tall. Your `Horizontal` uses `1fr`, so it takes every row nothing else has claimed.

Typical layout:

```python
def compose(self):
    yield Header()
    with HorizontalGroup(id="toolbar"):  # auto height
        yield Button("New")
        yield Button("Open")
    with Horizontal(id="body"):          # fills the rest
        with Vertical(id="sidebar"):
            ...
        with Vertical(id="main"):
            ...
    yield Footer()
```

```css
#sidebar { width: 30; }
#main    { width: 1fr; }
#toolbar { height: 3; }   /* optional: pin the height instead of auto */
```

If you want a different height, set `height` yourself: a fixed number or `auto` on a `Horizontal`, or a fixed number on a `HorizontalGroup`. Also, don't put children with `height: 1fr` inside a container with `height: auto`. Their heights depend on each other and can't be resolved, so they collapse.

To see what's happening, run `textual run --dev app.py` with `textual console` open, or press `Ctrl+P` and choose the inspector/devtools. It shows the computed size of each widget.
