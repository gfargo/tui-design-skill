**Yes—calling `app.Draw()` from a background goroutine is supported while the event loop is running. But directly updating a `Table` there is unsafe.** `Draw()` doesn’t protect earlier table mutations from concurrent rendering or input handling.

Poll the API in your goroutine, then apply the result through `QueueUpdateDraw`:

```go
// In your polling goroutine:
rows, err := fetchRows()
if err != nil {
    // Handle the error.
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

Keep API calls outside the closure, and don’t concurrently modify the data it reads. No additional `app.Draw()` is needed.

Deadlocks come from **waiting on work that cannot proceed**:

- **Calling `Draw`, `QueueUpdate`, or `QueueUpdateDraw` from an event-loop callback or a queued update.** These methods enqueue work and wait for completion. The event loop is stuck inside your callback, so it cannot execute that work.
- **Re-entering application locks during drawing.** Drawing holds the application mutex, including during before/after draw hooks. Calling a method that acquires that mutex—such as `SetRoot`, `SetFocus`, or `Stop`—from such a hook can deadlock.
- **Holding your own mutex while waiting for a queued update**, when the update or drawing needs the same mutex. Similar cycles occur if a UI callback waits for a worker that is waiting for the UI.
- **Queuing work without a running event loop.** Calls before `Run()` block until the loop starts; calls after it exits can wait indefinitely.

In ordinary input callbacks, update widgets directly; tview redraws after handling input. If an immediate redraw is necessary there, `ForceDraw()` is available, but don’t call it from a background goroutine or recursively from draw hooks.

One documentation trap: the current `QueueUpdate` comment suggests calling `Draw()` inside its closure. **The implementation makes that deadlock**: `Draw()` calls the blocking `QueueUpdate()` again. Use `QueueUpdateDraw()` instead. These details follow the [current source](https://github.com/rivo/tview/blob/master/application.go) and [concurrency guidance](https://github.com/rivo/tview/wiki/Concurrency).