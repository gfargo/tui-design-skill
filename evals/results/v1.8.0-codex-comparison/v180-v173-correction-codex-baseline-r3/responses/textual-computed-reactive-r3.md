`display` is already a Textual widget property: a boolean controlling whether the widget is displayed. Your `compute_display()` collides with that built-in name, and `self.display` returns the visibility flag (`True`), not your text.

For this simple case, render directly from the reactive count:

```python
count = reactive(0)

def render(self):
    return f"Count: {self.count}"
```

If you want a computed reactive value, give it a distinct name and declare it:

```python
count = reactive(0)
count_text = reactive("")

def compute_count_text(self):
    return f"Count: {self.count}"

def render(self):
    return self.count_text
```