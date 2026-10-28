There are two separate problems here.

## 1. `items.append()` doesn't trigger anything

Textual reactives work by intercepting **attribute assignment** (`__set__`). When you call `self.items.append(x)`, you change the list in place, so no assignment happens. Textual never sees the change, so it doesn't call `watch_items` and doesn't repaint.

You can fix this in either of two ways.

**Option A: Reassign a new list.** This is simple and always works:

```python
self.items = [*self.items, x]
```

Because the new list compares unequal to the old one, the watcher fires and the widget refreshes.

**Option B: Mutate the list, then tell Textual about it.** This needs Textual 0.66 or later:

```python
self.items.append(x)
self.mutate_reference(MyWidget.items)
```

`mutate_reference` runs the watchers and the refresh even though the object's identity hasn't changed. It's the better choice when the list is large or you're making several changes in a row. Make all the changes first, then call it once.

Be careful with Option A if you copy the list in some other way and the result is equal to the old one. Watchers only fire when `old != new`, unless you declare the reactive with `always_update=True`.

## 2. Change `cursor` without repainting

Declare it with `var` instead of `reactive`:

```python
from textual.reactive import reactive, var

class MyWidget(Widget):
    items: reactive[list[str]] = reactive(list)
    cursor: var[int] = var(0)        # no repaint, no layout

    def watch_cursor(self, old: int, new: int) -> None:
        ...  # still fires, so you can react here if needed
```

`var` behaves just like `reactive`: you still get validation, `watch_` methods and `compute_`. The only difference is that it never triggers a refresh. `reactive(0, repaint=False)` does the same thing if you'd rather be explicit.

If the cursor does need to show something on screen, like a highlighted row, don't repaint the whole widget. In `watch_cursor`, refresh only the affected lines, for example with `self.refresh(Region(...))` for the old and new rows. Alternatively, update a child widget's class with `child.set_class(...)` so Textual only restyles that child.

## Putting it together

```python
class ItemList(Widget):
    items: reactive[list[str]] = reactive(list)
    cursor: var[int] = var(0)

    def add_item(self, x: str) -> None:
        self.items.append(x)
        self.mutate_reference(ItemList.items)   # fires watch_items + repaint

    def watch_items(self, items: list[str]) -> None:
        self.cursor = min(self.cursor, max(len(items) - 1, 0))

    def action_down(self) -> None:
        self.cursor += 1                          # no repaint
```
