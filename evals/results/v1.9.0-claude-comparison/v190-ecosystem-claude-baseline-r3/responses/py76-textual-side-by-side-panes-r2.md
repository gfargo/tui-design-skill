Both problems come from Textual's layout defaults, not from your widths.

## 1. Sidebar and main stack vertically

`width` only sets how wide a widget is. Whether siblings sit side by side or stack is decided by the **parent's `layout`**. Widgets you yield straight from `App.compose` go onto the Screen, and the Screen's default is `layout: vertical`. So you get a 30-column sidebar with a full-width main area below it.

Either put them inside a horizontal container:

```python
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical

class MyApp(App):
    CSS_PATH = "app.tcss"

    def compose(self) -> ComposeResult:
        with Horizontal(id="body"):
            yield Vertical(id="sidebar")
            yield Vertical(id="main")
```

Or change the Screen's layout, which only makes sense if nothing else is on the Screen:

```css
Screen { layout: horizontal; }
```

The wrapper is usually the better choice because it still works once you add a header, toolbar or footer.

## 2. HorizontalGroup vs Horizontal

These two are designed to differ only in height. Their default CSS:

| Container | Default CSS |
|---|---|
| `Horizontal` | `width: 1fr; height: 1fr; layout: horizontal;` |
| `HorizontalGroup` | `width: 1fr; height: auto; layout: horizontal;` |

- **`Horizontal` fills the screen** because `height: 1fr` takes all the remaining vertical space. That's what you want for the main body.
- **`HorizontalGroup` is one row** because `height: auto` shrinks it to fit its tallest child. If the toolbar holds Labels, or other widgets that are 1 line tall, the toolbar is 1 line tall. It can also collapse if its children use `height: 1fr`, because inside an auto-height parent there's no spare space for `fr` to divide.

So: use `HorizontalGroup` for toolbars and `Horizontal` for the area that should fill the screen. Then set the toolbar height if the content doesn't give you the height you want.

## Putting it together

```python
from textual.containers import Horizontal, HorizontalGroup, Vertical
from textual.widgets import Button, Footer, Header

def compose(self) -> ComposeResult:
    yield Header()
    with HorizontalGroup(id="toolbar"):
        yield Button("New")
        yield Button("Open")
        yield Button("Save")
    with Horizontal(id="body"):        # takes all remaining height
        yield Vertical(id="sidebar")
        yield Vertical(id="main")
    yield Footer()
```

```css
#toolbar {
    height: 3;            /* or leave auto; Buttons are 3 rows tall anyway */
}
#toolbar Button {
    height: 3;            /* avoid 1fr on children of an auto-height parent */
    min-width: 8;
}

#sidebar { width: 30; }
#main    { width: 1fr; }
```

In a vertical layout, `fr` heights split whatever is left after fixed and `auto` heights are laid out. Here the header, toolbar and footer take their rows, and `#body` gets the rest. If you add a second `1fr` sibling, it and `#body` will split that space evenly.

To check what's actually being applied, run `textual run --dev app.py` with `textual console` open. Or press `ctrl+p` and use the inspector to see each widget's computed `layout`, `width` and `height`.
