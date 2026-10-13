**Yes—calling `app.Draw()` from a background goroutine is safe. But it doesn’t make concurrent `Table` updates safe.** Queue the table changes and redraw together:

```go
// In your polling goroutine:
rows, err := fetchRows(ctx) // Network work stays outside the UI loop.
if err != nil {
    // Handle/report the error.
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

Keep `rows` stable until the queued update completes. Calling `table.SetCell(...)` directly from the worker and then `app.Draw()` can race with rendering or input handling.

The main deadlock trap is **calling back into the UI queue from the UI loop itself**:

- A key handler, input capture, or selection callback calls `Draw()`, `QueueUpdate()`, or `QueueUpdateDraw()`.
- A queued update calls another queue method or `Draw()`.
- A drawing callback calls one of those methods.

These calls wait for the main loop to process queued work, but that loop is still executing your callback and cannot proceed. In ordinary input callbacks, change the widgets directly; tview redraws after handling the event. Inside `QueueUpdateDraw`, just make the changes—the wrapper supplies the redraw.

Another deadlock comes from your own locks: a worker holds a mutex while waiting for `QueueUpdateDraw`, and the UI needs that same mutex to finish processing or drawing. Release locks before making blocking queue calls. Likewise, don’t make a UI callback wait for a worker that is waiting on the UI queue.

Queue calls also require a running event loop; before `Run()` or after shutdown, they can wait indefinitely. Tie polling to the application lifecycle.

See tview’s [Concurrency guidance](https://github.com/rivo/tview/wiki/Concurrency).