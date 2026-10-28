Both problems have the same cause. Width and height in TCSS only size a widget. Whether children go side by side or stack depends on the **parent's `layout`**, and each container class has its own default height.

## 1. Sidebar and main stack vertically

When you yield `#sidebar` and `#main` straight from `App.compose`, their parent is the **Screen**, and the Screen uses `layout: vertical` by default. So `width: 30` and `width: 1fr` are applied, but each pane still goes on its own row: a 30-cell-wide sidebar, with main below it at full width.

You can fix it either way below.

**Option A: make the Screen horizontal.** This is a CSS-only change:

```css
Screen {
    layout: horizontal;
}

#sidebar { width: 30; }
#main    { width: 1fr; }
```

**Option B: wrap the panes in a `Horizontal`.** Use this if the Screen also holds things that should stack, like a toolbar above the panes:

```python
from textual.app import App, ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical
from textual.widgets import Button, Footer, Header

class MyApp(App):
    CSS_PATH = "app.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with HorizontalGroup(id="toolbar"):
            yield Button("New")
            yield Button("Open")
        with Horizontal(id="body"):
            yield Vertical(id="sidebar")
            yield Vertical(id="main")
        yield Footer()
```

I'd go with **B** for a real app. The Screen stays a vertical stack (header, toolbar, body, footer) and only the body splits into columns. With option A, every child of the Screen becomes a column, including your toolbar.

## 2. HorizontalGroup shrinks and Horizontal fills the screen

This is how the classes are designed:

| Container | Default size | Use for |
|---|---|---|
| `Horizontal`, `Vertical`, `Grid` | `width: 1fr; height: 1fr` (takes all remaining space) | Pane regions, like `#body` above |
| `HorizontalGroup`, `VerticalGroup`, `ItemGrid` | `height: auto` (as tall as its tallest child) | Toolbars, form rows, button bars |

- **The `HorizontalGroup` is one row tall** because its children are one row tall. Labels and compact widgets are 1 row; a default `Button` is 3. If you want a fixed toolbar height, set it: `#toolbar { height: 3; }`.
- **The `Horizontal` fills the screen** because `height: 1fr` takes all the space left over. That's correct for `#body` and wrong for a toolbar. If you used `Horizontal` for the toolbar, change it to `HorizontalGroup`, or override it with `#toolbar { height: auto; }`.

So: use a group for anything that should fit its content, and a plain container for the region that should fill the rest. With the layout above you get:

```
┌ Header ─────────────────────────────────────────┐
│ [New] [Open]                     ← HorizontalGroup, auto height
├──────────┬──────────────────────────────────────┤
│ #sidebar │ #main                ← Horizontal, 1fr height
│  30 cols │  1fr                                 │
│          │                                      │
└──────────┴──────────────────────────────────────┘
  Footer
```

## Also check narrow terminals

A fixed `width: 30` sidebar leaves 50 columns for `#main` in an 80-column terminal, but only 30 in a 60-column tmux split, which is too little for most content. At narrow widths, hide the sidebar and let `#main` take the full width:

```python
class MyApp(App):
    HORIZONTAL_BREAKPOINTS = [(0, "-narrow"), (70, "-wide")]
```

```css
.-narrow #sidebar { display: none; }
```

`display: none` removes the sidebar from the layout, so `#main`'s `1fr` takes the freed space. Give the user a key binding that opens the sidebar as an overlay or a separate screen, so its content can still be reached at narrow widths.

**Debugging tip:** run `textual run --dev app.py` with `textual console` open in another terminal, or add a temporary `border: solid red;` to each container. That shows each container's actual size and which parent it's under.
