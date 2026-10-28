Two separate problems, two fixes.

### 1. `append` doesn't trigger anything
Textual only notices **assignment** to a reactive. Changing the list in place (`append`, `extend`, `items[i] = ...`, `del`) leaves the same object in place, so no watcher runs and no repaint happens. After you mutate it, tell Textual:

```python
self.items.append(x)
self.mutate_reactive(MyWidget.items)   # runs watch_items, validators, and repaints
```

(`mutate_reactive` needs Textual 0.62 or newer.) Pass the class attribute (`MyWidget.items`), not `self.items`.

The other option is to assign a new list:

```python
self.items = [*self.items, x]
```

Don't write `self.items = self.items` after the append. Textual compares the old and new values, they're the same object, so nothing fires.

Keep `reactive(list)` with the callable default as you have it. That gives each widget instance its own list.

### 2. `cursor` shouldn't repaint the widget
Use `var` instead of `reactive`. A `var` still runs `watch_cursor`, but it never refreshes or re-lays-out the widget:

```python
from textual.reactive import reactive, var
from textual.widget import Widget

class MyWidget(Widget):
    items: reactive[list[str]] = reactive(list)
    cursor = var(0)          # watchers fire, no repaint

    def watch_items(self, items: list[str]) -> None:
        ...  # e.g. clamp cursor
        self.cursor = min(self.cursor, max(len(items) - 1, 0))

    def watch_cursor(self, old: int, new: int) -> None:
        ...  # update a status label, scroll into view, etc.

    def add_item(self, x: str) -> None:
        self.items.append(x)
        self.mutate_reactive(MyWidget.items)
```

One catch: if the cursor is drawn by this same widget (a highlighted row in `render()`), then cursor moves need to repaint it. In that case either keep `cursor` as a `reactive` and accept the repaint (it's cheap), or keep it as a `var` and call `self.refresh()` in `watch_cursor` only when the visible highlight actually changes. If `refresh()` turns out to be expensive, the usual fix is to split the cursor highlight into its own small widget, so cursor moves don't repaint the whole list.
