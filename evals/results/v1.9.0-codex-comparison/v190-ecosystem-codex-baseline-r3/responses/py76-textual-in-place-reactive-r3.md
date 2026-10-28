Textual detects **assignment** to a reactive attribute, not mutations inside a list. Replace the list when adding an item:

```python
from textual.reactive import reactive, var

class MyWidget(Widget):
    items: reactive[list[str]] = reactive(list)
    cursor: var[int] = var(0)

    def add_item(self, x: str) -> None:
        self.items = [*self.items, x]

    def watch_items(self, items: list[str]) -> None:
        # Respond to the new list.
        ...
```

Assigning a changed list triggers `watch_items` and schedules a repaint.

For `cursor`, `var(0)` is a reactive attribute that **does not automatically repaint**. Its watchers still run when it changes. Equivalently, use `reactive(0, repaint=False)`.

If you need to mutate the list in place, explicitly notify Textual afterward:

```python
self.items.append(x)
self.mutate_reactive(MyWidget.items)
```

Pass the class descriptor (`MyWidget.items`), not the list instance (`self.items`).