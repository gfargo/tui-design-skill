Use `exclusive=True` with a dedicated worker group, **and check cancellation before applying results**. Textual cancels earlier workers in the same group on the same widget, but it cannot forcibly stop a running thread.

```python
from textual import work
from textual.worker import Worker, get_current_worker
from textual.widgets import DataTable, Input

# Methods inside your App or Widget:

def on_input_changed(self, event: Input.Changed) -> None:
    self.search(event.value)

@work(thread=True, exclusive=True, group="search")
def search(self, query: str) -> None:
    worker = get_current_worker()
    if worker.is_cancelled:
        return

    rows = blocking_search(query)  # Your blocking search function

    if worker.is_cancelled:
        return

    self.app.call_from_thread(self.apply_results, worker, rows)

def apply_results(self, worker: Worker, rows: list[tuple]) -> None:
    # Check again on the UI thread: cancellation may have happened
    # after the worker queued this callback.
    if worker.is_cancelled:
        return

    table = self.query_one(DataTable)
    table.clear()  # Keep existing columns
    table.add_rows(rows)
```

The second check, **inside the UI callback**, closes the race that lets stale rows flicker into the table. All table changes must go through `self.app.call_from_thread(...)`.

For paginated searches, check `worker.is_cancelled` between blocking calls and guard every UI update the same way. An in-flight blocking call will still run until it returns; use timeouts or the search library’s cancellation support to bound that work.