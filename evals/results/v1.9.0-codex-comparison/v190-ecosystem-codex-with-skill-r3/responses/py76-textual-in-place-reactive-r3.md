Textual detects **assignment, not in-place list mutation**. After `append`, explicitly notify it with `mutate_reactive`. Use `var` for your cursor so changes can trigger watchers without automatically repainting or relaying out the widget.

```python
from textual.reactive import reactive, var
from textual.widget import Widget


class ItemsWidget(Widget):
    items: reactive[list[str]] = reactive(list)
    cursor: var[int] = var(0)

    def add_item(self, x: str) -> None:
        self.items.append(x)
        self.mutate_reactive(ItemsWidget.items)

    def watch_items(self, items: list[str]) -> None:
        self.log(f"{len(items)} items")

    def render(self) -> str:
        return "\n".join(self.items)
```

Pass the **class descriptor** (`ItemsWidget.items`) to `mutate_reactive`, not `self.items`. This fires watchers and schedules the reactive’s repaint.

Alternatively, replace the list through assignment:

```python
self.items = [*self.items, x]
```

Keep `reactive(list)`: its callable default gives each widget its own list. Cursor watchers can still cause a repaint if they explicitly call `refresh()` or update other UI state.