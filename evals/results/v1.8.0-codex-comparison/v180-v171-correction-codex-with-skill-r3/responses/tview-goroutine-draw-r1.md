**Yes, calling `app.Draw()` from a background goroutine is safe. Updating the `Table` directly from that goroutine is not.** `Draw()` schedules a repaint; it doesn’t synchronize widget mutations.

Fetch the API data in the worker, then apply the result on tview’s event loop:

```go
// In the polling goroutine:
rows, err := fetchRows() // Network I/O stays outside the UI loop.
if err != nil {
    // Handle or queue an error indication.
    return
}

app.QueueUpdateDraw(func() {
    table.Clear()
    for r, row := range rows {
        for c, value := range row {
            table.SetCell(r, c, tview.NewTableCell(value))
        }
    }
})
```

`QueueUpdateDraw` applies the changes and redraws, so no separate `Draw()` is needed. Keep `rows` stable while the callback uses it.

**Deadlocks come from waiting for the event loop while preventing it from progressing:**

- **Inside an input or selection callback:** calling `Draw()`, `QueueUpdate()`, or `QueueUpdateDraw()` waits for work that the same event loop must process. Mutate widgets directly there; normal input handling triggers redraw.
- **Inside a queued update:** nesting another queue call, or calling `Draw()`, creates the same circular wait.
- **Across your own locks or channels:** a worker holds a mutex while waiting for `QueueUpdateDraw`, but the UI needs that mutex; or a UI callback waits for a worker that is waiting for its queued update.

Queue calls wait until their callback completes. Release shared locks before queuing, keep queued callbacks short, and submit updates while `Run()` is active—calls before startup or after shutdown can wait indefinitely.

The distinction is: **a background redraw request is safe; background table mutation needs queuing; event-loop callbacks must not synchronously queue work back to themselves.**

See tview’s [Concurrency guide](https://github.com/rivo/tview/wiki/Concurrency).