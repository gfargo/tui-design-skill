You've run into a name collision. `display` is already a built-in property on every Textual widget, inherited from `DOMNode`. It controls whether the widget is shown, like the CSS `display: block`/`none`, and it returns a bool. So `self.display` gives you `True` because the widget is visible.

Your `compute_display` method never runs, for two reasons:

1. **Compute methods only work with a matching reactive.** Textual looks for `compute_<name>` only when the class declares a reactive called `<name>`. You didn't declare `display = reactive(...)`, so `compute_display` is just an ordinary method that nothing calls.
2. **Even if you declared one, you'd be overriding a core property.** That would break showing and hiding the widget.

**Fix:** use a name that isn't taken and declare it as a reactive:

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

For something this simple you can skip the computed reactive. `render()` runs again whenever `count` changes, because reactives refresh by default:

```python
def render(self) -> str:
    return f"Count: {self.count}"
```

Other names to avoid for reactives and attributes, since `Widget`/`DOMNode` already use them: `name`, `id`, `classes`, `styles`, `visible`, `disabled`, `size`, `region`, `parent`, `app`, `screen`, `children`, `log`.
