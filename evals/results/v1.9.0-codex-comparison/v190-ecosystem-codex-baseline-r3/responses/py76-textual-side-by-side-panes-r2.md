`width` controls size, not placement. `App.compose()` yields into Textual’s default `Screen`, which uses a **vertical layout**, so your two `Vertical` containers stack. A `Vertical` also controls the layout of its own children—not its placement beside siblings.

Put them inside a `Horizontal`:

```python
def compose(self) -> ComposeResult:
    with Horizontal(id="body"):
        yield Vertical(id="sidebar")
        yield Vertical(id="main")
```

```css
#body {
    width: 1fr;
    height: 1fr;
}

#sidebar {
    width: 30;
}

#main {
    width: 1fr;
}
```

Alternatively, if all direct children of the screen should sit side by side:

```css
Screen {
    layout: horizontal;
}
```

The toolbar behavior comes from **different default sizing**:

- `Horizontal` fills the available space by default, including height.
- `HorizontalGroup` uses `height: auto`, so its height follows its content—often one row. “Group” doesn’t mean it distributes the available screen height.

For a toolbar above a body, make the sizing explicit:

```python
def compose(self) -> ComposeResult:
    with HorizontalGroup(id="toolbar"):
        yield Button("Open")
        yield Button("Save")

    with Horizontal(id="body"):
        yield Vertical(id="sidebar")
        yield Vertical(id="main")
```

```css
Screen {
    layout: vertical;
}

#toolbar {
    height: auto;
}

#body {
    height: 1fr;
}

#sidebar {
    width: 30;
}

#main {
    width: 1fr;
}
```

You can use a regular `Horizontal` for the toolbar too; give it `height: auto` for content-sized height, or `height: 3` for a fixed three-row toolbar.