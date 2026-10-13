`display` is already Textual’s built-in boolean property controlling whether a widget participates in layout. `self.display` therefore returns `True`, not your text.

Also, `compute_<name>` requires a declared reactive attribute with the matching name; defining the method alone doesn’t create one.

Use a different name and declare it:

```python
from textual.reactive import reactive
from textual.widget import Widget

class Counter(Widget):
    count = reactive(0)
    count_text = reactive("")

    def compute_count_text(self) -> str:
        return f"Count: {self.count}"

    def render(self) -> str:
        return self.count_text
```

Textual recomputes `count_text` when `count` changes. For this simple case, you can also skip the computed attribute and return `f"Count: {self.count}"` directly from `render()`.