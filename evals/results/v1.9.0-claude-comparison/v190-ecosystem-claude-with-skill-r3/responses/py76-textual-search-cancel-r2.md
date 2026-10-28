Add `exclusive=True` and check for cancellation. With `exclusive=True`, starting a new search cancels the older workers in the same group. A thread worker can't be stopped from outside, though. Cancelling only marks it `CANCELLED`, and the thread keeps running. So the worker has to check `is_cancelled` itself and return before it writes to the table.

```python
from textual import work
from textual.widgets import DataTable, Input
from textual.worker import Worker, get_current_worker


def on_input_changed(self, event: Input.Changed) -> None:
    self.search(event.value)

@work(thread=True, exclusive=True, group="search", exit_on_error=False)
def search(self, query: str) -> None:
    worker = get_current_worker()
    for page in range(20):
        rows = slow_fetch(query, page)        # blocking call, can't be interrupted
        if worker.is_cancelled:               # a newer search replaced this one
            return
        self.app.call_from_thread(self.show_rows, worker, rows, page == 0)

def show_rows(self, worker: Worker, rows, first_page: bool) -> None:
    if worker.is_cancelled:                   # re-check on the UI thread (see below)
        return
    table = self.query_one(DataTable)
    if first_page:
        table.clear()
    table.add_rows(rows)
```

What each piece does:

- **`exclusive=True, group="search"`**: each new call cancels earlier workers in the `"search"` group on the same widget. Without a group, all exclusive workers share the default group, so a different exclusive worker could cancel your search, or the other way around.
- **`is_cancelled` in the thread**: checking after each blocking step lets a replaced search exit early instead of finishing work nobody will see.
- **`is_cancelled` again in `show_rows`**: the thread-side check alone still lets some stale rows through. A worker can pass its check, then the user types, then its `call_from_thread` callback runs anyway. Cancellation happens on the UI thread, and so does `show_rows`, so this second check can't race. It's what actually stops the flicker.
- **`self.app.call_from_thread`**: `call_from_thread` only exists on `App`. Inside a Screen or Widget, `self.call_from_thread` raises `AttributeError`.
- **`exit_on_error=False`**: a failed search won't crash the app. To show the error, handle `WorkerState.ERROR` in `on_worker_state_changed`. That message goes to the widget that started the worker and doesn't bubble.

**Optional: debounce.** If each search is expensive, a short delay before starting it avoids starting a thread for every character:

```python
def on_input_changed(self, event: Input.Changed) -> None:
    if self._debounce:
        self._debounce.stop()
    self._debounce = self.set_timer(0.2, lambda: self.search(event.value))
```

(Set `self._debounce = None` in `__init__` or `on_mount`.) The `exclusive` setup and the two cancellation checks are still needed, since the delay only cuts down how many workers start.
