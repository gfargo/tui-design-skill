`display` is already a Textual widget property: it’s a **boolean controlling visibility**, and defaults to `True`. So `self.display` reads that property, and `compute_display()` doesn’t turn it into your text.

Use a different name and declare it as reactive so Textual recognizes the computed value:

```python
count = reactive(0)
count_text = reactive("")

def compute_count_text(self) -> str:
    return f"Count: {self.count}"

def render(self) -> str:
    return self.count_text
```

Or, for something this simple, compute the text directly in `render()`:

```python
def render(self) -> str:
    return f"Count: {self.count}"
```

Changes to reactive `count` trigger a refresh automatically.