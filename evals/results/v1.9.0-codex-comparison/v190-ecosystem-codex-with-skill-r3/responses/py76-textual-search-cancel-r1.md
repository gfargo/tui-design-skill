Use **`exclusive=True` with a dedicated worker group**, and make cancellation cooperative. Textual cannot forcibly stop a running thread.

Also check cancellation **inside the UI callback**: a newer search can start after the thread checks cancellation but before its callback executes.

```python
from textual import on, work
from textual.worker import get_current_worker
from textual.widgets import DataTable, Input

# Methods on your App, Screen, or Widget:
@on(Input.Changed, "#search")
def search_changed(self, event: Input.Changed) -> None:
    self.search(event.value)

@work(thread=True, exclusive=True, group="search")
def search(self, query: str) -> None:
    worker = get_current_worker()
    if worker.is_cancelled:
        return

    rows = list(blocking_search(query))  # Your synchronous search

    if worker.is_cancelled:
        return

    def apply_results() -> None:
        # Runs on the UI thread; rejects stale callbacks too.
        if worker.is_cancelled:
            return
        table = self.query_one(DataTable)
        table.clear()  # Keeps columns
        table.add_rows(rows)

    self.app.call_from_thread(apply_results)
```

- **Replacement scope:** `exclusive=True` cancels earlier workers in the same group on the same owning widget.
- **Thread cancellation:** blocking work may continue until it returns. For paginated searches, check `worker.is_cancelled` between pages and before publishing each batch. Use I/O timeouts to bound blocking calls.
- **Thread safety:** update widgets through `self.app.call_from_thread(...)`; never directly from the worker thread.

Debouncing can reduce searches, but cancellation checks prevent stale results from appearing.