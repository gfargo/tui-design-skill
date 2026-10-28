Textual detects **assignment, not in-place mutation**. After appending, notify it with `mutate_reactive`. Use `var` for your cursor so changes still invoke watchers without automatically repainting or relaying out the widget.

```python
from textual.reactive import reactive, var
from textual.widget import Widget


class ItemList(Widget):
    items: reactive[list[str]] = reactive(list)
    cursor = var(0)

    def add_item(self, x: str) -> None:
        self.items.append(x)
        self.mutate_reactive(ItemList.items)

    def watch_items(self, items: list[str]) -> None:
        self.log(f"{len(items)} items")

    def render(self) -> str:
        return "\n".join(self.items)
```

Pass the **class descriptor** `ItemList.items` to `mutate_reactive`, not `self.items`. This triggers watchers and the normal reactive repaint.

Alternatively, replace the list through assignment:

```python
self.items = [*self.items, x]
```

Keep `reactive(list)`: the callable gives each widget its own list. Calling only `self.refresh()` would repaint, but wouldn’t trigger `watch_items`.