`display` is already a built-in property on every Textual widget. `Widget.display` is a `bool` that controls the CSS `display` style, i.e. whether the widget is shown. It returns `True` while the widget is visible, so `render()` returns `True` and that's what appears on screen.

Your `compute_display` never runs. Textual only calls a `compute_<name>` method when a reactive called `<name>` is declared on the class. You never declared a `display` reactive, so the method is ignored and `self.display` falls through to the built-in property.

**Fix:** use a name that doesn't clash and declare it as a reactive:

```python
from textual.reactive import reactive
from textual.widget import Widget

class Counter(Widget):
    count = reactive(0)
    label = reactive("")

    def compute_label(self) -> str:
        return f"Count: {self.count}"

    def render(self) -> str:
        return self.label
```

Don't fix it by declaring `display = reactive("")`. That would replace the built-in visibility property and break showing and hiding the widget.

For a simple case like this, you don't need a computed reactive at all. `render()` runs again whenever `count` changes, so you can format the text there:

```python
def render(self) -> str:
    return f"Count: {self.count}"
```

Other names already taken on `Widget` include `visible`, `styles`, `size`, `region`, `name`, `id` and `classes`. Avoid those for your own reactives or computed values.
