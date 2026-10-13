**Yes—`app.Draw()` is safe from a background goroutine while the event loop is running. But it does not make background `Table` mutations safe.** Queue the mutations and redraw together:

```go
// Inside the polling goroutine:
rows, err := fetchRows(ctx) // Network work stays outside the UI loop.
if err != nil {
    return // Or report the error through a queued UI update.
}

app.QueueUpdateDraw(func() {
    table.Clear()
    for r, row := range rows {
        table.SetCell(r, 0, tview.NewTableCell(row.Name))
    }
})
```

Keep `rows` stable until the queued update completes. No additional `app.Draw()` is needed.

The key detail is that **`Draw()` queues work and waits for completion**. `QueueUpdate` and `QueueUpdateDraw` also wait. Deadlocks arise from circular waits:

- **Event-loop callbacks queue and wait on their own loop.** Calling any of those three methods inside an input handler, selection callback running on the loop, or queued update blocks the loop that must execute the requested work. Mutate widgets directly in input callbacks; tview normally redraws afterward.
- **Draw callbacks re-enter application locks.** Drawing holds the application mutex. Before/after-draw callbacks calling methods that acquire that mutex can deadlock. Calling `ForceDraw()` there also attempts to acquire the same lock.
- **Your locks or waits form a cycle.** A worker holds a mutex while waiting for a queued update, and the UI needs that mutex; or the UI waits for a worker that is waiting for the UI.
- **The event loop is unavailable.** Queued calls can wait indefinitely before `Run()` starts or after it stops. Coordinate polling with application shutdown.

`ForceDraw()` draws immediately: reserve it for event-loop code when an immediate redraw is necessary, and avoid it in background goroutines or draw callbacks.

Directly calling `table.SetCell(...)` in the worker followed by `app.Draw()` creates a **data race**, even if it never deadlocks. The queued closure is what serializes table access.

These behaviors follow the [current implementation](https://github.com/rivo/tview/blob/master/application.go). Its `QueueUpdate` comment suggesting `Draw()` inside the closure conflicts with that implementation—use `QueueUpdateDraw()` instead.