Use `exclusive=True` so each new search cancels the previous one. **For thread workers, cancelling only sets a flag.** Python can't kill a running thread, so the old search keeps going unless your code checks that flag. Doing both fixes the flicker.

```python
from textual import work
from textual.worker import get_current_worker

class SearchApp(App):

    def on_input_changed(self, event: Input.Changed) -> None:
        self.run_search(event.value)

    @work(thread=True, exclusive=True, group="search")
    def run_search(self, query: str) -> None:
        worker = get_current_worker()

        results = []
        for row in expensive_search(query):      # your blocking search
            if worker.is_cancelled:              # stop early, saves CPU
                return
            results.append(row)

        self.call_from_thread(self._show_results, worker, results)

    def _show_results(self, worker, results) -> None:
        # Runs on the main thread. Cancellation also happens on the main
        # thread, so this check can't race with a newer search starting.
        if worker.is_cancelled:
            return
        table = self.query_one(DataTable)
        table.clear()
        table.add_rows(results)
```

Why each part matters:

1. **`exclusive=True, group="search"`**: starting a new `run_search` cancels any running worker in the `"search"` group. Give it a named group so it doesn't cancel unrelated workers in the default group.
2. **`is_cancelled` inside the loop**: a stale search stops early instead of running to completion. This is optional for correctness, but it keeps old searches from piling up and using CPU.
3. **`is_cancelled` in the main-thread callback**: this is the check that actually stops the flicker. If you only check in the thread before calling `call_from_thread`, a new search can start between that check and the UI update, and the stale rows still get in. Checking on the main thread closes that gap.
4. **Replace the whole result set at once**: call `clear()` and then add all the rows, rather than adding rows one by one from the thread. Rows added one at a time are another source of mixed results.

**Optional: debounce.** Running a search on every keystroke wastes work while the user is still typing. You can wait for a short pause first:

```python
def on_input_changed(self, event: Input.Changed) -> None:
    if self._debounce is not None:
        self._debounce.stop()
    self._debounce = self.set_timer(0.25, lambda: self.run_search(event.value))
```

(Set `self._debounce = None` in `__init__` or `on_mount`.)
