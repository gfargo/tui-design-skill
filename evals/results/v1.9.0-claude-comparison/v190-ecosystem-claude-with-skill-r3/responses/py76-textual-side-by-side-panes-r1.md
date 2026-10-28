**Both problems have the same cause: the parent decides the direction, and the container class decides the default height.**

## 1. The panes stack because `Screen` lays out vertically

A Textual `Screen` stacks its children top to bottom by default. Your `width: 30` and `width: 1fr` are working: the sidebar really is 30 cells wide. It just sits *above* `#main`. Each `Vertical` also defaults to `height: 1fr`, so they split the screen height in half.

Width rules don't change direction. You have to set direction on the **parent**. There are two ways:

**Option A: make the Screen horizontal** (fine when the panes are the only children)

```css
Screen {
    layout: horizontal;
}
#sidebar { width: 30; }
#main    { width: 1fr; }
```

**Option B: wrap the panes in a `Horizontal`** (better if you also have a `Header`, `Footer` or toolbar on the screen)

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
        with Horizontal(id="body"):          # ← this sets the direction
            with Vertical(id="sidebar"):
                ...
            with Vertical(id="main"):
                ...
        yield Footer()
```

With Option B the Screen stays vertical: header, toolbar, body, footer. `#body` puts the sidebar and main pane side by side, and since `Horizontal` is `height: 1fr`, it fills the space left over.

## 2. Group vs. non-group containers have different default heights

This behavior is intended:

| Container | Default size | Use for |
|---|---|---|
| `Vertical`, `Horizontal`, `Grid` | `width: 1fr; height: 1fr` (fill the space) | Panes and the main body |
| `VerticalGroup`, `HorizontalGroup`, `ItemGrid` | `height: auto` (shrink to content) | Toolbars, form rows, button bars |

- Your **`HorizontalGroup` toolbar** is as tall as its tallest child. With `Label`/`Static` children that's one row. A default `Button` is 3 rows, so the toolbar would be 3.
- Your **`Horizontal`** is `1fr`, so it takes all remaining height. If it comes before the toolbar, or nothing else claims space, it takes the whole screen.

Fixes, depending on what you want:

```css
/* The toolbar hugs its content (usually right): keep HorizontalGroup.
   If you want a fixed height instead: */
#toolbar { height: 3; }

/* If you used Horizontal for the toolbar, make it hug its content: */
#toolbar { height: auto; }

/* To pin the toolbar no matter where it is in compose order: */
#toolbar { dock: top; }
```

As a rule: use a `Group` for anything that should be as tall as its content, and a plain container for regions that should fill space. Use exactly one `1fr` region per axis, unless you deliberately want to split the space.

## The narrow-terminal case

A fixed `width: 30` sidebar leaves only 30 columns for `#main` in a 60-column tmux split, and that's too tight for most content. Pick a column width (say 80) below which you hide the sidebar or switch to a single pane. For example, you can toggle a class on resize:

```python
def on_resize(self, event) -> None:
    self.query_one("#body").set_class(event.size.width < 80, "narrow")
```

```css
#body.narrow #sidebar { display: none; }
```

Then add a key binding to show the sidebar again as an overlay or drill-down, so the narrow layout doesn't cut off navigation.
