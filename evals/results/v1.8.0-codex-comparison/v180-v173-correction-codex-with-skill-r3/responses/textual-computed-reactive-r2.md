`display` is already Textual’s built-in boolean property controlling whether a widget participates in layout. `self.display` therefore returns `True`, rather than your count text.

Also, `compute_<name>()` needs a declared reactive attribute with the same name. Use a different name and declare it:

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

For this simple case, you can skip the computed reactive entirely:

```python
def render(self) -> str:
    return f"Count: {self.count}"
```

Changing the reactive `count` automatically triggers a repaint.