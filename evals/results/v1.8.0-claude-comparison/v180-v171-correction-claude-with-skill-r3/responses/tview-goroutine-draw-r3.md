**Short answer:** Calling `app.Draw()` from your polling goroutine won't deadlock, but it isn't safe for what you're doing. `Draw()` only asks for a repaint. It does nothing to stop your goroutine's `Table` edits from racing with the main loop while it renders that same table. Do the table update and the redraw together with `app.QueueUpdateDraw`.

## The pattern

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

        rows, err := fetchRows(ctx) // network I/O stays OUT of the main loop
        if err != nil {
            continue // or queue an error-banner update
        }

        app.QueueUpdateDraw(func() { // runs on tview's main goroutine
            table.Clear()
            for r, row := range rows {
                for c, v := range row {
                    table.SetCell(r, c, tview.NewTableCell(v))
                }
            }
        })
    }
}
```

- Do the slow work (HTTP request, parsing) in the goroutine. Hand only the finished data into the closure. Anything slow inside the closure freezes the UI, because input handling waits for it.
- Inside the closure you're on the main goroutine, so you can touch any primitive. Outside it, don't change any widget: no `SetCell`, `Select`, `SetTitle`, and so on. (`TextView` is an exception: its `Write` is safe from other goroutines.)
- Run `go test -race` or `go run -race` once. A bare `SetCell` from the goroutine shows up immediately as a race with `Table.Draw`.

## Where deadlocks come from

`QueueUpdate`, `QueueUpdateDraw` and `Draw` send work to the main event loop and then **block until the main loop has run it**. Every tview deadlock follows from that:

1. **Calling them from the main goroutine (the #1 cause).** Key handlers (`SetInputCapture`, `SetSelectedFunc`, `SetDoneFunc`, `SetChangedFunc`), the body of a `QueueUpdate` closure, and `SetBeforeDrawFunc`/`SetAfterDrawFunc` all run on the main loop. If one of them calls `app.Draw()` or `QueueUpdateDraw()`, the loop waits for itself and hangs. In a handler you don't need either: change the widget directly and tview redraws once the handler returns.
   ```go
   table.SetSelectedFunc(func(r, c int) {
       status.SetText("selected")   // fine
       // app.QueueUpdateDraw(...)  // deadlock
       // app.Draw()                // deadlock (per tview's docs)
   })
   ```
   A variant of this: a helper like `refreshTable()` that calls `QueueUpdateDraw` works fine from the poller, but hangs as soon as someone calls it from a key handler too. Either keep main-loop and background helpers separate, or have the helper take the data and let callers decide how to dispatch it.

2. **A lock held across the queue call.** Suppose the poller holds `mu` while it calls `QueueUpdateDraw`, and a key handler on the main loop also does `mu.Lock()`. The poller waits for the main loop and the main loop waits for `mu`. Release your own locks before you queue anything, or copy the data under the lock and queue the copy.

3. **Queueing when no loop is running.** If you call `QueueUpdateDraw` before `app.Run()` starts, or after `app.Stop()`, nothing processes it and the goroutine blocks, possibly for good. On shutdown that leaks the goroutine and can hang anything that waits on it, such as a `WaitGroup`. Cancel the poller's context before or right after `Stop()`, as the `ctx.Done()` check above does.

4. **Blocking on something the main loop owns.** For example, a handler waits on a channel that only the poller sends to, while the poller sits inside `QueueUpdateDraw`. Same circular wait as #2, just with a channel instead of a lock.

## Rule of thumb

| You are in… | To change a widget | To repaint |
|---|---|---|
| A background goroutine | `app.QueueUpdateDraw(func(){…})` | included in the line to the left |
| A handler or callback (main loop) | change it directly | automatic, never call `Draw()` |

This matches the threading rule in the skill's `references/ecosystem-go.md` (tview section), which follows tview's Concurrency wiki.
