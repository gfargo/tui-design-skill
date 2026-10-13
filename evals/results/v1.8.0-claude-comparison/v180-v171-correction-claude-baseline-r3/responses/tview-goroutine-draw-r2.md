**Short answer:** calling `app.Draw()` from a background goroutine won't deadlock, but it doesn't protect the table either. The unsafe part is changing the table (`SetCell`, `Clear`, …) from that goroutine. The event loop may be drawing that same table at the same moment, which is a data race. Do the changes inside `app.QueueUpdateDraw`:

```go
go func() {
    ticker := time.NewTicker(5 * time.Second)
    defer ticker.Stop()
    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
        }

        rows, err := fetchRows(ctx) // slow I/O stays off the UI goroutine

        app.QueueUpdateDraw(func() {
            // Runs on the event-loop goroutine; touching primitives is safe here.
            if err != nil {
                status.SetText("[red]" + err.Error())
                return
            }
            row, col := table.GetSelection()
            table.Clear()
            for r, rec := range rows {
                for c, v := range rec {
                    table.SetCell(r, c, tview.NewTableCell(v))
                }
            }
            table.Select(row, col) // keep the user's place
        })
    }
}()
```

Rules of thumb:
- **Fetch outside the closure, change the UI inside it.** Anything slow inside the closure freezes the UI.
- **Use `QueueUpdateDraw` rather than `QueueUpdate` followed by `Draw()`.** It does both in one step.
- **Run with `go run -race` / `go test -race`.** If you're calling `SetCell` directly from the poller, the race detector will flag it right away.

## Where tview deadlocks actually come from

`QueueUpdate` and `QueueUpdateDraw` **block until the event loop has run your function**. Almost every tview deadlock comes from that.

1. **Calling `QueueUpdate*` or `Draw()` from the event-loop goroutine.** Code there is waiting for the event loop, which is itself, so it never returns. This happens in places that don't look like the "main thread":
   - `SetInputCapture` and `SetInputHandler` functions
   - widget callbacks: `SetSelectedFunc`, `SetSelectionChangedFunc`, `SetDoneFunc`, `SetChangedFunc`, button handlers, etc.
   - code inside another `QueueUpdate` closure
   - callbacks fired *indirectly*. For example, `table.Select()` inside your queued closure fires `SetSelectionChangedFunc`. If that callback calls `QueueUpdateDraw`, it hangs.

   The fix is simple: inside callbacks, change the primitives directly. The event loop redraws after every event anyway, so you never need `Draw()` there.

2. **Your own mutex, taken from both sides.** Suppose the poller holds `mu` while calling `QueueUpdateDraw`, and some input handler also takes `mu`. Then the poller waits for the event loop while the event loop waits for `mu`. Release your locks before queuing, or copy the data out first and hand it over by value through the closure.

3. **Queuing when no event loop is running.**
   - *Before `app.Run()` starts:* set up the initial state directly, or start the poller after `Run` is up.
   - *After `app.Stop()`:* the poller can get stuck in `QueueUpdateDraw` and either leak or hang shutdown. Cancel the poller's `ctx` before or when you call `Stop()`, as the `select` above does.

4. **Blocking work in handlers.** This isn't a true deadlock, but it looks like one. A network call or a channel send inside an input handler freezes the whole UI. Start a goroutine and report back with `QueueUpdateDraw`.

The model to keep in mind: one goroutine owns the widgets. Every other goroutine sends it closures through `QueueUpdateDraw`, and code already running on that goroutine never sends one to itself.
