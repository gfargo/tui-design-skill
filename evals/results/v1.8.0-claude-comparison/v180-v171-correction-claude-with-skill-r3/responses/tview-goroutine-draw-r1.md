**Short answer:** Yes, you can call `app.Draw()` from a background goroutine. It only schedules a repaint, though. It does nothing to make your Table edits safe. tview deadlocks happen in the other direction: when you call `Draw`/`QueueUpdate`/`QueueUpdateDraw` from code that is already running on tview's main loop.

## Updating the Table from the poller

tview widgets have no locks, and `Table` is no exception. If your goroutine calls `table.SetCell(...)` directly, it races with the main loop, which may be reading those same cells to draw them. `app.Draw()` afterwards doesn't fix that, because the data race has already happened.

Do the slow work (the API call) on the goroutine. Then hand the widget changes to the main loop with `QueueUpdateDraw`:

```go
go func() {
    ticker := time.NewTicker(5 * time.Second)
    defer ticker.Stop()
    for range ticker.C {
        rows, err := fetchRows(ctx) // slow work: off the UI thread
        app.QueueUpdateDraw(func() { // widget mutation: on the UI thread
            if err != nil {
                status.SetText("[red]fetch failed: " + err.Error())
                return
            }
            table.Clear()
            for r, row := range rows {
                for c, v := range row {
                    table.SetCell(r, c, tview.NewTableCell(v))
                }
            }
        })
    }
}()
```

The rule is: anything that changes a widget from a goroutine goes through `QueueUpdate` or `QueueUpdateDraw`. A bare `Draw()` from a goroutine is only right when the data the widget renders is already synchronized some other way. (`TextView` is the exception: its `Write` is safe to call concurrently.)

## Where deadlocks come from

`QueueUpdate` puts your function on the event loop's update queue and **waits for it to finish**. `Draw()` and `QueueUpdateDraw()` go through the same queue. So:

1. **Calling them from a handler (the #1 pitfall).** Key handlers (`SetInputCapture`, `SetDoneFunc`), `SetSelectedFunc`, `SetChangedFunc`, `SetFocusFunc`, the draw hooks (`SetBeforeDrawFunc`/`SetAfterDrawFunc`) and the body of a `QueueUpdate` all already run on the main goroutine. If one of them calls `app.QueueUpdateDraw(...)` or `app.Draw()`, it waits for the loop to run the update. But the loop is stuck waiting for that handler to return, so it never does. The fix is to change the widget directly inside the handler. tview redraws after the event anyway, so you don't need to call `Draw` at all.

2. **Holding your own lock across a queued call.** The goroutine takes `mu.Lock()` and calls `QueueUpdateDraw` while still holding it. Meanwhile a key handler on the main loop tries to take `mu`. Each side now waits on the other. Copy what you need under the lock, unlock, and only then queue the update.

3. **Queuing when no loop is running.** A `QueueUpdate` made before `app.Run()` has started, or after `app.Stop()`, has nothing to execute it, so the goroutine blocks forever. This often shows up as a hang on shutdown. Start the poller after the app is set up, and stop it with a `context` that you cancel before or when you call `Stop()`.

4. **Shared helpers called from both sides.** A helper like `refreshTable()` that does `QueueUpdateDraw` internally works fine from the poller and hangs when called from a key binding. Split it into a plain `renderTable(rows)` that edits widgets directly, plus a thin wrapper for goroutines that queues it.

**What to remember:** goroutines queue their updates, and handlers modify widgets directly. Never queue from code that's already on the main loop.
