Use `exclusive=True` to cancel the previous worker in the same group. **Thread cancellation is cooperative**: the old thread must check `worker.is_cancelled` and stop publishing results.

```python
from textual import work
from textual.worker import Worker, get_current_worker

@work(thread=True, exclusive=True, group="search")
def search(self, query: str) -> None:
    worker = get_current_worker()
    rows = []

    for result in run_search(query):
        if worker.is_cancelled:
            return
        rows.append(result)

    if not worker.is_cancelled:
        self.call_from_thread(self.show_results, worker, rows)

def show_results(self, worker: Worker, rows: list) -> None:
    # Check again on the UI thread: cancellation may have happened
    # while this callback was waiting to run.
    if worker.is_cancelled:
        return

    table = self.query_one(DataTable)
    table.clear()
    table.add_rows(rows)
```

Call `self.search(event.value)` from your input change handler.

The explicit group keeps cancellation scoped to searches. `exclusive=True` marks older searches as cancelled; it cannot forcibly interrupt a running thread or a blocking search call. Those may finish in the background, but the cancellation checks prevent their stale rows from reaching the table. Always update Textual widgets through `call_from_thread` when working in a thread.