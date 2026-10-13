**Yes, calling `app.Draw()` from a background goroutine is safe. But it does not make concurrent `Table` updates safe.** Queue the table mutations onto tview’s event loop and redraw together:

```go
// Inside your polling goroutine:
rows, err := fetchRows() // Network work stays outside the UI loop.
if err != nil {
    // Handle/report the error.
    return
}

app.QueueUpdateDraw(func() {
    table.Clear()
    for r, row := range rows {
        table.SetCell(r, 0, tview.NewTableCell(row.Name))
        table.SetCell(r, 1, tview.NewTableCell(row.Status))
    }
})
```

Keep `rows` stable until the queued update completes. Avoid this pattern:

```go
table.SetCell(...) // Can race with rendering/input.
app.Draw()         // Does not synchronize that mutation.
```

The classic deadlock comes from **calling `Draw()`, `QueueUpdate()`, or `QueueUpdateDraw()` inside a callback already executing on the UI loop**, such as an input handler or `SetSelectedFunc`. These calls queue work and wait for the loop to process it; the loop cannot proceed until your callback returns. Nested queue calls inside a queued update have the same problem.

In an event handler, mutate widgets directly and return; normal input processing redraws. For API work triggered by a handler, launch a worker and have that worker call `QueueUpdateDraw()` when its result is ready.

Another deadlock source is holding your own mutex while waiting for a queued update whose callback—or rendering—needs that mutex. Copy the data and release the lock before queuing. Queue calls also need an active event loop, so coordinate polling with startup and shutdown.

See tview’s [Concurrency guidance](https://github.com/rivo/tview/wiki/Concurrency).