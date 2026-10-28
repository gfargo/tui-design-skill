Use **`exclusive=True` with a dedicated worker group**, plus cooperative cancellation and a guard against stale UI updates.

Textual cancels previous workers in the same group on the same DOM node, but **cancelling a thread worker doesn’t kill its thread**. The worker must check `is_cancelled`; blocking calls may keep running until they return.

```python
from textual import work
from textual.worker import get_current_worker
from textual.widgets import DataTable, Input

# Inside your App or widget:
_search_version = 0

def on_input_changed(self, event: Input.Changed) -> None:
    self._search_version += 1
    self.search(event.value, self._search_version)

@work(thread=True, exclusive=True, group="search")
def search(self, query: str, version: int) -> None:
    worker = get_current_worker()
    rows = []

    for row in search_backend(query):  # Your blocking search
        if worker.is_cancelled:
            return
        rows.append(row)

    if worker.is_cancelled:
        return

    # Widget mutations must run on the UI thread.
    self.call_from_thread(self._apply_search, version, rows)

def _apply_search(self, version: int, rows) -> None:
    # Check here too: a newer search may have started while
    # this update was waiting to run on the UI thread.
    if version != self._search_version:
        return

    table = self.query_one(DataTable)
    table.clear()
    table.add_rows(rows)
```

The version check prevents old results from appearing, even when a backend call cannot be interrupted. If you stream rows individually instead, apply the same check inside every UI callback.