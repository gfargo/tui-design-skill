Use `exclusive=True` on the worker, and check for cancellation inside the worker yourself.

### 1. Make the worker exclusive

```python
@work(thread=True, exclusive=True, group="search")
def run_search(self, query: str) -> None:
    ...
```

With `exclusive=True`, starting a new worker cancels any running workers in the same `group`. The default group is `"default"`, so a named group keeps this from cancelling your other workers.

### 2. Check for cancellation yourself

Python can't kill a thread, so Textual can't stop a thread worker. Cancelling only sets `worker.is_cancelled = True`, and the old thread keeps running. That's why stale rows still show up. Your code has to check the flag and stop:

```python
from textual import work
from textual.worker import Worker, get_current_worker

class SearchApp(App):
    def on_input_changed(self, event: Input.Changed) -> None:
        self.run_search(event.value)

    @work(thread=True, exclusive=True, group="search")
    def run_search(self, query: str) -> None:
        worker = get_current_worker()
        results = []
        for row in do_search(query):      # ideally an iterator / chunked work
            if worker.is_cancelled:       # bail out early, saves CPU
                return
            results.append(row)
        self.call_from_thread(self.show_results, worker, results)

    def show_results(self, worker: Worker, results: list) -> None:
        # Runs on the main thread. Check again here: the worker may have been
        # cancelled between the loop finishing and this callback running.
        if worker.is_cancelled:
            return
        table = self.query_one(DataTable)
        table.clear()
        table.add_rows(results)
```

Key points:
- **Run the final check in the main-thread callback.** New workers are started and old ones cancelled on the main thread. That makes the check inside `show_results` the reliable one. A check in the thread just before `call_from_thread` can still race.
- **Send all rows in one batch** with `clear()` + `add_rows()`. If you add rows one at a time from the thread, you'll get partial updates and flicker even without stale workers.
- **Check `is_cancelled` often** in long loops so old searches stop using CPU quickly. If `do_search` is one blocking call, such as a single DB query, it will run to completion. Its result is simply thrown away.

### 3. Optional: debounce keystrokes

To avoid starting a search on every key press, wait for a short pause in typing:

```python
def on_input_changed(self, event: Input.Changed) -> None:
    if self._search_timer is not None:
        self._search_timer.stop()
    self._search_timer = self.set_timer(0.25, lambda: self.run_search(event.value))
```

(Set `self._search_timer = None` in `__init__` or `on_mount`.)

Use exclusive workers with the cancellation checks to fix the flicker. Debouncing is extra: it cuts down how many searches start in the first place.
