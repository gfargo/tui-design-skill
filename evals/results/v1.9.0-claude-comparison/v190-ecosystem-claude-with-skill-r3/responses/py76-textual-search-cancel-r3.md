Use `exclusive=True` so each new search cancels the previous one, and have the thread check whether it was cancelled before it touches the table.

```python
from textual import work
from textual.widgets import DataTable, Input
from textual.worker import get_current_worker

def on_input_changed(self, event: Input.Changed) -> None:
    self.search(event.value)

@work(thread=True, exclusive=True, group="search", exit_on_error=False)
def search(self, query: str) -> None:
    worker = get_current_worker()
    for page in range(20):
        rows = slow_fetch(query, page)
        if worker.is_cancelled:  # a newer search replaced this one
            return
        self.app.call_from_thread(self.show_rows, worker, rows)

def show_rows(self, worker, rows) -> None:
    if worker.is_cancelled:  # cancelled between the check and this call
        return
    self.query_one(DataTable).add_rows(rows)
```

**Why `exclusive=True` alone isn't enough:**
- `exclusive=True` cancels earlier workers in the same `group` on the same widget (or app).
- An async worker stops at its next `await`. A thread worker can't be interrupted, though. Cancelling it only sets its state to `CANCELLED`, and the thread keeps running. That's why old rows still show up after a newer search starts.
- So the thread has to check `get_current_worker().is_cancelled` after every slow step and return before updating the UI.
- `show_rows` runs on the UI thread and checks again. A new keystroke can cancel the worker after the thread's check but before the queued update runs, and this second check covers that gap.

**Other details:**
- Use `self.app.call_from_thread(...)` to update the UI from a thread. That method only exists on `App`, so inside a Screen or Widget, `self.call_from_thread` raises `AttributeError`.
- `exit_on_error=False` keeps one failed search from quitting the app. Handle the `ERROR` state in `on_worker_state_changed` on the widget that started the worker. That message doesn't bubble up.
- When a new search starts, clear the table (`table.clear()`) in `on_input_changed` before calling `self.search(...)`, so stale results don't stay on screen.
- If the search is expensive, debounce it. For example, restart a short `set_timer` (about 150–250 ms) on each keystroke and start the search when it fires. Typing quickly then launches one search instead of one per key.

If `slow_fetch` is I/O like HTTP, consider an async worker (`@work(exclusive=True)` with `httpx.AsyncClient`) instead. Cancellation then actually stops the request at the next `await`, rather than letting it run to completion in the background.
