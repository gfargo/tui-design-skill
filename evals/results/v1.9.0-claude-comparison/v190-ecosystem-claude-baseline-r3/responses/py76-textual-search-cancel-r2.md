Use `exclusive=True` on the decorator, and **also** check for cancellation inside the thread before you touch the table.

### Why `exclusive=True` alone isn't enough

`@work(exclusive=True)` cancels any earlier worker in the same **group** when a new one starts. That fully stops async workers. Python can't kill a running thread, though, so for a thread worker cancelling only sets a flag (`worker.is_cancelled`). Your old search keeps running to the end and still posts its rows, which is the flicker you're seeing. The thread has to check that flag itself.

### Fix

```python
from textual import work
from textual.worker import get_current_worker
from textual.widgets import DataTable, Input


class SearchApp(App):
    def on_input_changed(self, event: Input.Changed) -> None:
        self.run_search(event.value)

    @work(thread=True, exclusive=True, group="search")
    def run_search(self, query: str) -> None:
        worker = get_current_worker()

        results = []
        for row in search_backend(query):   # your slow search
            if worker.is_cancelled:          # bail out early if a newer search started
                return
            results.append(row)

        if not worker.is_cancelled:          # final check before touching the UI
            self.call_from_thread(self.show_results, results)

    def show_results(self, results: list[tuple]) -> None:
        table = self.query_one(DataTable)
        table.clear()
        table.add_rows(results)
```

Key points:

1. **`exclusive=True, group="search"`**: The default group is `"default"`, so without your own group name, a new search would also cancel any other exclusive worker in that group. A dedicated group limits cancellation to searches.
2. **Check `is_cancelled` inside the loop**: The stale thread stops early instead of using CPU or I/O on a result nobody will see.
3. **Check it again right before updating the UI**: This is what actually stops the flicker. A worker can be cancelled after its last loop check but before it posts results.
4. **Update the UI with `call_from_thread`**: Widgets aren't thread-safe. Batching the rows into one `clear()` plus `add_rows()` call also stops rows appearing one at a time.

### Optional: debounce

If each search is expensive, add a short pause at the start of the worker so fast typing doesn't start a search on every keystroke:

```python
import time

    @work(thread=True, exclusive=True, group="search")
    def run_search(self, query: str) -> None:
        worker = get_current_worker()
        time.sleep(0.2)                 # wait for typing to pause
        if worker.is_cancelled:
            return
        ...
```

Each new keystroke cancels the sleeping worker, so only the last query after a 200 ms pause actually runs.

If your search backend can be awaited (an async HTTP client or database driver), consider an async worker (`@work(exclusive=True)` without `thread=True`). Cancellation then really interrupts it at the next `await`, and you don't need the manual checks.
