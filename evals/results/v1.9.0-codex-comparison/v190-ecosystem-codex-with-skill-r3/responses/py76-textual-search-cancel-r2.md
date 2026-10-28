Use `exclusive=True` with a dedicated worker group, then **cooperatively check cancellation**. Textual cancels earlier workers in the same group on the same widget, but it cannot forcibly stop a running thread.

Also check cancellation inside the UI callback: a new search may start after the thread checks but before its callback runs.

```python
from textual import work
from textual.worker import get_current_worker
from textual.widgets import DataTable, Input

# Methods on your App (or the widget that owns the searches):

def on_input_changed(self, event: Input.Changed) -> None:
    self.search(event.value)

@work(thread=True, exclusive=True, group="search")
def search(self, query: str) -> None:
    worker = get_current_worker()

    if worker.is_cancelled:
        return

    rows = slow_search(query)  # Your blocking search function

    if worker.is_cancelled:
        return

    self.app.call_from_thread(self.apply_results, worker, rows)

def apply_results(self, worker, rows) -> None:
    # Runs on the UI thread; reject superseded results here too.
    if worker.is_cancelled:
        return

    table = self.query_one(DataTable)
    table.clear()  # Keep existing columns
    table.add_rows(rows)
```

For a paginated search, check `worker.is_cancelled` before and after each blocking fetch, and guard every UI update the same way. Use `self.app.call_from_thread(...)` for UI mutations; `post_message(...)` is another thread-safe option.

An in-flight blocking call still runs until it returns. Give network calls timeouts and use the underlying library’s cancellation support where available. Debouncing reduces work, but cancellation checks prevent stale results from appearing.