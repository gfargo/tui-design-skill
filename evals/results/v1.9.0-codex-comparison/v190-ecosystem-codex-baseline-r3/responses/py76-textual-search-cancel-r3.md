Use `exclusive=True` to cancel the previous worker in the same group. Because thread workers cannot be forcibly stopped, also check cancellation before publishing results.

```python
from textual import work
from textual.worker import get_current_worker
from textual.widgets import DataTable, Input

def on_input_changed(self, event: Input.Changed) -> None:
    self.search(event.value)

@work(thread=True, exclusive=True, group="search")
def search(self, query: str) -> None:
    worker = get_current_worker()
    rows = []

    for row in blocking_search(query):
        if worker.is_cancelled:
            return
        rows.append(row)

    def publish() -> None:
        # Check here too: cancellation may happen while this
        # callback is waiting to run on the UI thread.
        if worker.is_cancelled:
            return

        table = self.query_one(DataTable)
        table.clear()
        table.add_rows(rows)

    self.call_from_thread(publish)
```

The two parts serve different purposes:

- **`exclusive=True`** marks older workers in `"search"` as cancelled when a new one starts.
- **`worker.is_cancelled`** makes the thread cooperate and prevents stale results from reaching the table.

If `blocking_search()` is one long blocking call, it may keep running until it returns. You can still discard its results afterward. Always update Textual widgets on the UI thread via `call_from_thread()`.