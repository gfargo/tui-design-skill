You need two changes. Add `exclusive=True` to the decorator, and make the thread check whether it has been cancelled before it touches the table.

```python
from textual import work
from textual.worker import get_current_worker

@work(thread=True, exclusive=True, group="search", exit_on_error=False)
def search(self, query: str) -> None:
    worker = get_current_worker()
    for page in range(20):
        rows = slow_fetch(query, page)
        if worker.is_cancelled:      # a newer search replaced this one
            return
        self.app.call_from_thread(self.show_rows, query, rows)

def show_rows(self, query: str, rows) -> None:
    # Runs on the UI thread. Drop results from a query the user has already typed past.
    if query != self.query_one(Input).value:
        return
    self.query_one(DataTable).add_rows(rows)
```

**Why `exclusive=True` alone doesn't fix it:**

- `exclusive=True` cancels any earlier worker in the same `group` on the same widget when a new one starts. Name the group (here `"search"`) so this doesn't also cancel your other workers.
- An async worker stops at its next `await`. A thread worker can't be interrupted, though. Cancelling it only sets its state to `CANCELLED`, and the thread keeps running. That's why old searches keep adding rows to your table. The thread has to poll `get_current_worker().is_cancelled` and return on its own.
- Check it after each slow step (each page, chunk or I/O call) and right before every `call_from_thread`. A long blocking call can't be cut short, but its results get thrown away.

**The check in `show_rows`:** A worker can pass the `is_cancelled` check and then get cancelled before its queued `call_from_thread` runs. Comparing `query` to the current input value on the UI thread throws those late results away, so nothing old can reach the table.

**Other things to know:**

- `call_from_thread` exists only on `App`. Inside a Screen or Widget, use `self.app.call_from_thread(...)`.
- With `exit_on_error=False`, a failed search won't quit the app. Handle the `ERROR` state in `on_worker_state_changed` on the widget that started the worker. That message goes to the widget and doesn't bubble up.
- Clear the table when a new search starts (for example, in your `on_input_changed` before calling `self.search(value)`), so old rows don't stay on screen while the new search runs.
- If each search is expensive, you could also debounce the keystrokes, for example with a short `set_timer` that you reset on each change. `exclusive=True` keeps the results correct, and debouncing cuts down on wasted searches.
