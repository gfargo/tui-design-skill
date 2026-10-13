## Why you see `True`

There are two problems, and together they produce exactly what you're seeing.

**1. `display` is already a built-in property on every widget.** `Widget.display` is a boolean that controls whether the widget is shown (it maps to the CSS `display: block | none`). So `self.display` in your `render()` returns that flag, which is `True` because the widget is visible. That's what gets rendered.

**2. `compute_display` never runs.** Textual only calls `compute_<name>` methods for attributes declared as `reactive` (or `var`) on the class. You never declared `display = reactive(...)`, so Textual ignores the method. Declaring it wouldn't help, though, because it would overwrite the built-in `display` property and break showing and hiding the widget.

## Fix

Give it a name that doesn't clash and declare it as a reactive:

```python
from textual.reactive import reactive
from textual.widget import Widget

class Counter(Widget):
    count = reactive(0)
    label = reactive("")          # must be declared for compute_label to run

    def compute_label(self) -> str:
        return f"Count: {self.count}"

    def render(self) -> str:
        return self.label
```

Textual tracks that `compute_label` reads `self.count`. When `count` changes, it recomputes `label` and refreshes the widget.

For something this simple you don't need a computed reactive at all. `render()` already runs again whenever a reactive changes, because reactives have `repaint=True` by default:

```python
class Counter(Widget):
    count = reactive(0)

    def render(self) -> str:
        return f"Count: {self.count}"
```

Before naming a reactive, check that the name isn't already used by `Widget` or `DOMNode`. Names like `display`, `visible`, `styles`, `name`, `id`, `classes`, `size`, `region`, `app`, `parent` and `children` are all taken, and reusing them causes subtle bugs like this one.
