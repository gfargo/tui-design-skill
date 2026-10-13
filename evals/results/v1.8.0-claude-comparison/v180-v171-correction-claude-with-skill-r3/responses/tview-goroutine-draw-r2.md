**Short answer:** yes, calling `app.Draw()` from your polling goroutine is safe. It doesn't make your Table update safe, though. The deadlocks come from the opposite case: calling these methods from code that is already running on tview's main goroutine.

## Draw() repaints but doesn't protect your data

`Draw()` queues a repaint on the main event loop, so calling it from another goroutine is fine. But if your goroutine does this:

```go
// RACE: table is being mutated off the main goroutine
table.Clear()
for i, row := range rows {
    table.SetCell(i, 0, tview.NewTableCell(row.Name))
}
app.Draw()
```

then the main loop may be drawing the Table, or a key handler may be reading it, while you're changing its cells. That's a data race. Expect torn rendering, occasional index-out-of-range panics, and failures under `go test -race`.

**The rule:** any change to a primitive from another goroutine goes through `QueueUpdate` or `QueueUpdateDraw`. Both run your function on the main loop.

```go
func poll(ctx context.Context, app *tview.Application, table *tview.Table) {
    t := time.NewTicker(5 * time.Second)
    defer t.Stop()
    for {
        select {
        case <-ctx.Done():
            return
        case <-t.C:
        }

        rows, err := fetchRows(ctx) // slow I/O stays HERE, off the UI thread

        app.QueueUpdateDraw(func() { // only cheap widget changes inside
            if err != nil {
                table.SetTitle(" error: " + err.Error() + " ")
                return
            }
            table.Clear()
            for i, r := range rows {
                table.SetCell(i, 0, tview.NewTableCell(r.Name))
                table.SetCell(i, 1, tview.NewTableCell(r.Status))
            }
        })
    }
}
```

Do the network call outside the callback and only touch widgets inside it. If the HTTP request runs inside `QueueUpdateDraw`, the whole UI freezes until it returns.

## Where the deadlocks come from

`QueueUpdate` and `QueueUpdateDraw` put your function on the main loop's update channel, then block until the main loop has run it. In current tview, `Draw()` also queues its work this way. So if you call any of the three from code the main loop is already running, it waits for itself and hangs.

That code includes:
- `SetInputCapture` and other key handlers
- `SetSelectedFunc`, `SetChangedFunc`, `SetDoneFunc`, button and form callbacks
- functions you passed to `QueueUpdate` or `QueueUpdateDraw` (don't nest them)
- `SetBeforeDrawFunc` and `SetAfterDrawFunc`

```go
table.SetSelectedFunc(func(row, col int) {
    table.GetCell(row, col).SetTextColor(tcell.ColorRed)
    app.QueueUpdateDraw(func() {}) // DEADLOCK: we're already on the main goroutine
    app.Draw()                     // same problem
})
```

You don't need either call there. tview redraws by itself after an event handler returns, so just change the widget directly.

A quick test for which to use:

| You are in…                         | Change widgets with…              |
|-------------------------------------|-----------------------------------|
| A tview callback or handler         | Direct calls; no Draw needed      |
| Your own goroutine                  | `app.QueueUpdateDraw(func(){…})`  |

## Two related hangs

- **Shutdown:** a poller can call `QueueUpdateDraw` after `app.Stop()`, when the main loop is no longer reading updates. Since the call waits for the main loop to run it, the goroutine can block forever. Pass a `context` to the poller and cancel it before or alongside `Stop()`, as in the example above.
- **A handler that waits on the poller:** suppose a key handler does `<-resultCh` and the poller is itself blocked in `QueueUpdateDraw`. Each is waiting on the other. A handler should start the work in a goroutine and let that goroutine report back with `QueueUpdateDraw`; it shouldn't wait for the result itself.

**Sources:** tview's Concurrency wiki page, and the tview section of the skill's `references/ecosystem-go.md`. It's worth running `go run -race` or `go test -race` once with the poller active. Any direct Table change you missed will show up there.
