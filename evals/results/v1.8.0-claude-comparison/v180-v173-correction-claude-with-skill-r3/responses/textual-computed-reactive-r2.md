You're seeing `True` because `self.display` isn't your computed value. It's a property that every Textual `Widget` already has.

**Two things combine to cause it:**

1. **`display` is already taken.** `Widget.display` controls whether the widget is visible. It's a bool tied to the CSS `display` style, where `True` means anything other than `display: none`. So `render()` returns `True`, and Textual draws it as text.

2. **`compute_display` never runs.** A `compute_<name>` method only takes effect when you also declare a reactive called `<name>` on the class. You declared `count` but not `display`, so Textual ignores `compute_display` and treats it as an ordinary method that nothing calls.

**Don't fix it by declaring `display = reactive("")`.** That would hide the built-in visibility property, and `widget.display = False` and the CSS `display` rule would stop working properly.

**Fix:** pick a different name and declare it as a reactive:

```python
from textual.reactive import reactive
from textual.widget import Widget

class Counter(Widget):
    count = reactive(0)
    label = reactive("")          # the compute target must be declared

    def compute_label(self) -> str:
        # read-only derived value, recomputed when count changes
        return f"Count: {self.count}"

    def render(self) -> str:
        return self.label
```

`label` is now read-only and recalculated whenever `count` changes. When you assign to a reactive, Textual runs **validate → assign → watch → compute**, then refreshes the widget so `render()` shows the new text.

Other built-in `Widget` attributes are also easy to hit by accident, such as `visible`, `styles`, `size`, `region`, `name`, `id` and `disabled`. If a reactive or computed value behaves strangely, check that its name isn't one of these.
