`display` is already Textual’s built-in boolean property controlling whether a widget participates in layout. It defaults to `True`, so `self.display` returns that boolean.

Also, `compute_<name>()` needs a declared reactive attribute with the matching name; the method alone doesn’t create one. Choose a different name and declare it:

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

For this simple case, you can skip the computed attribute entirely:

```python
def render(self) -> str:
    return f"Count: {self.count}"
```

Changing `count` automatically triggers a repaint.