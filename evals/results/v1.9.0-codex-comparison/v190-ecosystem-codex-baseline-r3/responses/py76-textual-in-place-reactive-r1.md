Textual detects **assignment** to a reactive attribute, not mutations inside a list. Replace the list to trigger `watch_items` and the default repaint:

```python
from textual.reactive import reactive, var

class MyWidget(Widget):
    items: reactive[list[str]] = reactive(list)
    cursor: var[int] = var(0)

    def add_item(self, x: str) -> None:
        self.items = [*self.items, x]

    def watch_items(self, items: list[str]) -> None:
        ...
```

If you need to mutate the list in place, explicitly notify Textual afterward:

```python
self.items.append(x)
self.mutate_reactive(MyWidget.items)
```

Use `var(0)` for `cursor`: it supports reactive watchers but doesn’t automatically repaint or trigger layout. Alternatively, use `reactive(0, repaint=False)`.