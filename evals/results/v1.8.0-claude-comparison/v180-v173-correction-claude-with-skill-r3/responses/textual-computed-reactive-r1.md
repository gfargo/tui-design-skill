There are two problems here:

1. **`display` is already a built-in `Widget` property.** It controls whether the widget is shown. It's `True` when the widget is visible, and setting it to `False` removes the widget from layout. So `self.display` returns that visibility flag, not your text.

2. **`compute_display` never runs.** Textual only calls `compute_<name>` when there's a reactive declared with that same name. You didn't declare a `display` reactive, so `compute_display` is just an ordinary method that nothing calls.

Your `render()` reads the visibility flag, gets `True`, and shows it.

**Fix:** declare a reactive under a name that isn't taken, and give its compute method the same name:

```python
from textual.reactive import reactive
from textual.widget import Widget

class Counter(Widget):
    count: reactive[int] = reactive(0)
    label: reactive[str] = reactive("")

    def compute_label(self) -> str:
        # Recomputed automatically when count changes
        return f"Count: {self.count}"

    def render(self) -> str:
        return self.label
```

Some things to know about compute methods:
- A computed reactive is read-only, so don't assign to `self.label` yourself.
- When you assign to a reactive, Textual runs validate, then assign, then watch, then compute.
- Avoid other names `Widget` already uses, like `visible`, `styles`, `size` or `region`, for the same reason.

For something this simple you don't need a computed reactive. `count` already triggers a repaint when it changes, so this works too:

```python
def render(self) -> str:
    return f"Count: {self.count}"
```
