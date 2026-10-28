Textual only notices when you **assign** to a reactive. It doesn't see changes made inside the object. `self.items.append(x)` changes the same list object in place, so the reactive's setter never runs. That's why no watcher fires and nothing repaints. The fix is to tell Textual about the change, and to make `cursor` a `var`.

```python
from textual.reactive import reactive, var
from textual.widget import Widget

class ItemList(Widget):
    items: reactive[list[str]] = reactive(list)  # callable default: one list per widget
    cursor = var(0)                              # watchers fire, no repaint

    def add_item(self, x: str) -> None:
        self.items.append(x)                     # in-place: invisible to Textual...
        self.mutate_reactive(ItemList.items)     # ...so fire watchers + repaint by hand

    def watch_items(self, old: list[str], new: list[str]) -> None:
        ...  # note: after mutate_reactive, old and new are the same list object

    def watch_cursor(self, old: int, new: int) -> None:
        ...  # side effects only; the widget is not repainted
```

## `items`: two ways to fix it

1. **`self.mutate_reactive(ItemList.items)`** after `append`, `extend`, `d[k] = v`, `sort()` and so on. Pass the class attribute, not `self.items`. Textual then runs the watchers and repaints. It's the cheapest option for large lists because nothing is copied. One catch: `watch_items(old, new)` gets the same object twice, so you can't diff `old` against `new`. If you need the previous value, keep it yourself.
2. **Assign a new list:** `self.items = [*self.items, x]`. This goes through the normal path: validate → assign → watch → compute. The watcher fires because the new list doesn't equal the old one. Use this when you want a real `old`/`new` pair. It costs a copy of the list on every change.

If adding items changes the widget's size (for example, `height: auto`), declare it with `reactive(list, layout=True)`. Otherwise the widget repaints but isn't resized.

## `cursor`: use `var`

`var(0)` keeps validators and watchers but never triggers a repaint or a layout pass. It's meant for exactly this kind of value: a cursor index or a cache.

There's a catch: if the cursor *is drawn* (for example, a highlighted row), something still has to update the screen. Don't make `cursor` a full `reactive` again. Update only the part that changed in `watch_cursor`. Pick one:
- If each row is its own child widget, toggle a CSS class on the old row and the new row (`row.set_class(True, "-highlight")`). Only those two rows repaint.
- If you draw rows yourself with the Line API (`render_line`), call `self.refresh(Region(0, old, self.size.width, 1), Region(0, new, self.size.width, 1))` to repaint just those two lines.
- If the list can grow beyond a few hundred rows, don't build your own. Use `OptionList` or `ListView`, which already handle the highlighted row and only draw what's on screen.

## Testing

You can test this without a terminal. Run the widget with `App.run_test()` and the pilot, call `add_item`, then check that `watch_items` ran (a counter or a flag works) and that the rendered output contains the new item. Also check that pressing the up/down keys changes `cursor` without calling the widget's `render`.
