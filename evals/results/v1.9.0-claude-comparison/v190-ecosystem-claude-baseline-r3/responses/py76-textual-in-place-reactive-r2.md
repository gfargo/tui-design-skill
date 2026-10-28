## Why `watch_items` doesn't fire

Textual only notices a change to a reactive when you **assign** to the attribute. `self.items.append(x)` changes the list in place, so the descriptor's `__set__` never runs. That means no watcher, no validation and no refresh.

Even `self.items = self.items` won't work. Textual compares the old and new values, and they're the same object, so it skips the update.

## Fix for `items`

**Option A: tell Textual you mutated it** (Textual ≥ 0.62):

```python
self.items.append(x)
self.mutate_reactive(MyWidget.items)   # runs watchers and repaints
```

**Option B: assign a new list:**

```python
self.items = [*self.items, x]
```

Option B is often cleaner because the watcher's `old` and `new` arguments are actually different objects:

```python
def watch_items(self, old: list[str], new: list[str]) -> None:
    ...
```

With `mutate_reactive`, `old` and `new` are the same list. If your watcher diffs them, use Option B.

Keep `reactive(list)` with the factory as you have it. A bare `reactive([])` would share one list across all instances.

## Fix for `cursor`

Use `var`. It's a reactive with `repaint=False` and `layout=False`, so watchers and validators still run but assigning to it never triggers a refresh:

```python
from textual.reactive import reactive, var

class MyWidget(Widget):
    items: reactive[list[str]] = reactive(list)
    cursor: var[int] = var(0)

    def watch_cursor(self, old: int, new: int) -> None:
        # Optional: repaint only what changed, e.g. two lines
        # self.refresh(Region(0, old, self.size.width, 1),
        #              Region(0, new, self.size.width, 1))
        ...
```

`reactive(0, repaint=False)` does the same thing if you'd rather be explicit.

One caveat: if `render()` uses `cursor`, the highlight won't move on screen until something else triggers a repaint. Either refresh just the affected region from `watch_cursor` (as in the comment above) or move the cursor highlight into a child widget, so each move only repaints a small piece.
