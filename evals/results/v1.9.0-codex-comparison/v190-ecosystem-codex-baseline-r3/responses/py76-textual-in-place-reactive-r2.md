Textual detects **assignment** to a reactive attribute, but `append()` mutates the existing list without assigning it. Assign a new list to trigger `watch_items` and a repaint:

```python
items: reactive[list[str]] = reactive(list)
cursor: reactive[int] = reactive(0, repaint=False)

def add_item(self, x: str) -> None:
    self.items = [*self.items, x]

def watch_items(self, items: list[str]) -> None:
    ...
```

If you need to mutate the list in place, explicitly notify Textual afterward:

```python
self.items.append(x)
self.mutate_reactive(MyWidget.items)  # Replace MyWidget with your class
```

`repaint=False` on `cursor` keeps its reactive behavior, including watchers, while preventing cursor changes from automatically repainting the widget.