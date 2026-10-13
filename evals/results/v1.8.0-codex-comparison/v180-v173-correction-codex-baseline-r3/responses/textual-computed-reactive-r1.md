`display` is already a Textual `Widget` property: a boolean controlling whether the widget is displayed. Your `compute_display()` collides with that built-in property, so `self.display` gives you a boolean instead of your text.

Use a different name for your computed reactive:

```python
class Counter(Widget):
    count = reactive(0)
    count_text = reactive("")

    def compute_count_text(self) -> str:
        return f"Count: {self.count}"

    def render(self) -> str:
        return self.count_text
```

Or just format the value in `render()`—changes to `count` trigger a repaint by default:

```python
def render(self) -> str:
    return f"Count: {self.count}"
```