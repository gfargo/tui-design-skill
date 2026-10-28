Textual reactives only notice **assignment**. `self.items.append(x)` changes the list in place, so the descriptor never runs. No watcher fires and no refresh is triggered.

## Fix for `items`

**Option A: tell Textual you mutated it** (Textual ≥ 0.70-ish has `mutate_reactive`):

```python
def add_item(self, x: str) -> None:
    self.items.append(x)
    self.mutate_reactive(MyWidget.items)   # runs watch_items and refreshes
```

**Option B: assign a new list:**

```python
self.items = [*self.items, x]
```

This works because the new list compares unequal to the old one. One trap: `self.items.append(x); self.items = self.items` does **not** work. The old and new values are the same object, so they compare equal and Textual skips the update. You'd need `reactive(list, always_update=True)` for that to fire, so Option A or B is cleaner.

## Fix for `cursor`

Use `var` (or `reactive(..., repaint=False)`). It's still observable, so watchers fire, but changing it doesn't refresh the widget:

```python
from textual.reactive import reactive, var
from textual.widget import Widget

class MyWidget(Widget):
    items: reactive[list[str]] = reactive(list)   # repaints on change
    cursor: var[int] = var(0)                      # no repaint

    def watch_items(self, old: list[str], new: list[str]) -> None:
        ...

    def watch_cursor(self, old: int, new: int) -> None:
        # still called; do targeted work here if needed
        ...
```

Quick reference:
- `reactive(...)`: `repaint=True`, `layout=False` by default.
- `var(...)`: no repaint and no layout, but watchers and validators still run.
- `reactive(..., layout=True)`: use this when the change affects size, so a refresh alone isn't enough.

**Caveat:** if `render()` actually draws the cursor (a highlighted row, for example), you'll need *some* refresh when it moves. In that case, keep it as a `var` and call `self.refresh(region)` in `watch_cursor` for just the old and new rows. You can also move the cursor display into a small child widget so only that part repaints.
