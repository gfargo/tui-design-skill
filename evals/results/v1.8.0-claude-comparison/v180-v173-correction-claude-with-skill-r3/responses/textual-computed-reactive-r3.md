The name `display` is already taken by Textual, so your compute method never runs.

**What's going on**

1. **`Widget.display` is a built-in property.** It's a shortcut for the CSS `display` rule. Reading it returns a bool: `True` when the widget is visible, `False` when `display: none`. So `render()` returns `True`, and that's what gets drawn.
2. **`compute_<name>` only works when there's a matching reactive.** Textual hooks up `compute_foo` only if the class declares `foo = reactive(...)`. Your class has no `display` reactive, so `compute_display` is just an ordinary method that nothing calls.

Even if you did declare `display = reactive("")`, you'd be overwriting the attribute Textual uses to show and hide the widget. That would break visibility.

**Fix: use a name that isn't taken**

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

`label` is recalculated whenever `count` changes. Since it's a reactive, the widget then refreshes.

**A simpler option:** for a value that's only used for display, you can skip the computed reactive:

```python
class Counter(Widget):
    count = reactive(0)

    def render(self) -> str:
        return f"Count: {self.count}"
```

Changing `count` already triggers a refresh, so `render()` runs again on its own.

**Other names to avoid** for reactives and attributes, because `Widget` already uses them: `display`, `visible`, `styles`, `id`, `name`, `classes`, `disabled`, `size`, `region`, `parent`, `app`, `screen`, `children`, `content`, `renderable`.
