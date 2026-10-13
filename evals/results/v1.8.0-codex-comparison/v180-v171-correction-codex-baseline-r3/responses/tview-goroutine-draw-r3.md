**Yes—calling `app.Draw()` from your background goroutine is safe while the event loop is running. But updating a `Table` directly from that goroutine is not.** `Draw()` does not synchronize the preceding table mutations. Queue the mutations and redraw together: citeturn829526view1

```go
// In the polling goroutine:
rows, err := fetchRows() // Keep network I/O outside the UI update.
if err != nil {
    return // Or handle the error.
}

app.QueueUpdateDraw(func() {
    table.Clear()
    for r, row := range rows {
        for c, value := range row {
            table.SetCellSimple(r, c, value)
        }
    }
})
```

Keep `rows` stable until this call returns.

The central deadlock mechanism is **waiting for the event loop from code already executing on that loop**. `QueueUpdate` enqueues a function and blocks until it finishes; `Draw()` uses `QueueUpdate` internally. citeturn829526view0

Common causes:

- **Calling `Draw()`, `QueueUpdate()`, or `QueueUpdateDraw()` inside an input handler or a queued update.** The loop waits for work that only that same loop can execute. In input callbacks, mutate the table directly; tview redraws after handling the event.
- **Holding your own mutex while making a blocking queue call**, when the queued function or drawing code needs that mutex. Release it first and pass a snapshot.
- **Reentering application methods from drawing callbacks.** Drawing holds the application mutex. For example, calling `ForceDraw()` or a method needing that mutex inside a before/after-draw callback can deadlock.
- **Queuing work when `Run()` is not servicing updates**, such as after shutdown. The caller can wait indefinitely.

`ForceDraw()` draws immediately and is appropriate only in event-loop code when an immediate refresh is necessary; avoid it in background workers or during drawing itself.

There’s a misleading comment in the current `QueueUpdate` source suggesting calling `Draw()` inside its closure. The implementation would deadlock there. Use `QueueUpdateDraw()` instead. citeturn829526view0