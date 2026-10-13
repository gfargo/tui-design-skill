**Yes, calling `app.Draw()` from a background goroutine is safe.** That's what it's for. The real problem is changing the `Table` from that goroutine, and the deadlocks come from calling these functions from the wrong goroutine.

## What `Draw` and `QueueUpdate` do

In current tview, `Draw()` doesn't draw right away. It queues a draw on the application's event loop, the goroutine running `app.Run()`. `QueueUpdate(f)` and `QueueUpdateDraw(f)` work the same way: they send `f` to the event loop and **block until the loop has run it**. Keep that blocking behaviour in mind; it explains every deadlock below.

## The data race

```go
// WRONG: the event loop may be reading the table while this runs.
go func() {
    for range ticker.C {
        rows := fetch()
        for i, r := range rows {
            table.SetCell(i, 0, tview.NewTableCell(r.Name))
        }
        app.Draw()
    }
}()
```

`app.Draw()` is fine here. `table.SetCell` is not. Most tview widgets aren't goroutine-safe, so changing them off the event loop races with drawing and input handling. `go run -race` will flag it, and in practice it shows up as occasional garbled output or a panic.

## The correct pattern

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
        rows, err := fetch() // slow I/O stays OFF the event loop
        app.QueueUpdateDraw(func() {
            // runs on the event loop, so it's safe to touch widgets
            if err != nil {
                status.SetText(err.Error())
                return
            }
            table.Clear()
            for i, r := range rows {
                table.SetCell(i, 0, tview.NewTableCell(r.Name))
            }
        })
    }
}()
```

- Do the network call outside the closure. Anything inside it blocks input handling and redraws.
- `QueueUpdateDraw` does the update and the redraw in one call, so you don't need a separate `Draw()`.

## Where deadlocks come from

1. **Calling `QueueUpdate`, `QueueUpdateDraw` or `Draw` from the event loop itself.** The loop waits for its own queued function, which can't run until the loop is free, so it waits forever. The event loop is where these run:
   - `SetInputCapture` and widget input handlers
   - `SetSelectedFunc`, `SetChangedFunc`, `SetDoneFunc`, button callbacks, etc.
   - `SetBeforeDrawFunc` / `SetAfterDrawFunc`
   - the body of another `QueueUpdate` closure

   Inside these callbacks, change widgets directly. tview redraws automatically after an event handler returns, so `Draw()` isn't needed there.

2. **`TextView.SetChangedFunc(func() { app.Draw() })`.** This is the documented pattern when goroutines write to a `TextView`. But if you also write to that `TextView` from a handler on the event loop, the changed func fires on the loop and you hit case 1.

3. **Queuing before `Run()` starts or after `Stop()`.** If `main` calls `QueueUpdate` before `app.Run()`, it blocks forever because nothing is processing the queue yet. After `app.Stop()`, your poller's next `QueueUpdateDraw` hangs, which leaks the goroutine, or deadlocks if `main` waits for that goroutine (e.g. a `WaitGroup`). Cancel the poller (the `ctx` above) before or when you stop the app.

4. **Lock ordering with your own mutexes.** Say the poller holds `mu` while calling `QueueUpdateDraw`, and a key handler on the event loop also tries to take `mu`. Each side waits for the other. Never hold your own locks across a `QueueUpdate*` call. Copy the data out, unlock, then queue.

5. **Blocking channel operations inside handlers or closures.** If a handler sends on a channel that the poller reads, and the poller is currently blocked in `QueueUpdateDraw`, neither can make progress. Use buffered channels or `select` with a `default` case on the event-loop side.

**Rule of thumb:** off the event loop, only touch widgets inside `QueueUpdate` or `QueueUpdateDraw`. On the event loop, touch widgets directly and never call `QueueUpdate*` or `Draw()`. The tview wiki's "Concurrency" page says the same.
