The problem is that Textual only notices when you **assign** a new value to a reactive. `self.items.append(x)` changes the list in place, so the attribute is never reassigned. Nothing tells Textual to call `watch_items` or redraw. The fixes below come from the skill's Textual notes (`references/ecosystem-python.md`).

### 1. Tell Textual about the change with `mutate_reactive`

```python
from textual.reactive import reactive, var
from textual.widget import Widget

class ItemList(Widget):
    items: reactive[list[str]] = reactive(list)   # callable default: one list per widget
    cursor = var(0)                                # watchers fire, but no repaint

    def add_item(self, x: str) -> None:
        self.items.append(x)                       # in-place edits are invisible to Textual...
        self.mutate_reactive(ItemList.items)       # ...so fire watchers and repaint by hand

    def watch_items(self, old: list[str], new: list[str]) -> None:
        ...

    def watch_cursor(self, old: int, new: int) -> None:
        # still called on every change, but the widget isn't redrawn
        ...
```

Pass the class attribute (`ItemList.items`) to `mutate_reactive`, not `self.items`. The same applies to any in-place change: `d[k] = v`, `.sort()`, `del lst[i]` and so on.

You could also assign a new list: `self.items = [*self.items, x]`. Don't try `self.items = self.items`, though. Textual compares the old and new values before firing anything, and here they're the same object, so the watcher still won't run.

### 2. Use `var` for `cursor`

A `var` is a reactive with repaint and layout turned off. Watchers, validators and `data_bind` still work, but changing it doesn't redraw the widget. That suits a value that changes often, like a cursor index or a cache.

If you need more control, the options are:
- `reactive(0, repaint=False)`: the same as `var`, written out.
- `reactive(0, layout=True)`: use this when a change should also re-measure the widget's size.

### A caveat

If the cursor position is visible (a highlighted row, for example), something still has to redraw when it moves. In that case, do the work in `watch_cursor`: update just the affected child, call `self.refresh()` on the region that changed, or move a `ListView`/`OptionList`'s `highlighted`. That way each cursor move updates one row instead of redrawing the whole list.
