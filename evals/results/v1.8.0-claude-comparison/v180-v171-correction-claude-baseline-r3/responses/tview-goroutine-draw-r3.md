**Short answer:** Calling `app.Draw()` from a background goroutine won't crash, but it's the wrong tool. The real danger is **changing the Table from that goroutine**. tview widgets aren't thread-safe, so `table.SetCell(...)` from your poller is a data race whether or not you call `Draw()` afterwards.

## The right pattern

Do the slow work (the HTTP call) in the goroutine. Hand only the widget changes to the UI goroutine with `QueueUpdateDraw`:

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

		rows, err := fetchRows(ctx) // network I/O: off the UI goroutine
		if err != nil {
			continue
		}

		app.QueueUpdateDraw(func() { // runs on the event loop, then redraws
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

- `QueueUpdate(f)` runs `f` on the event-loop goroutine.
- `QueueUpdateDraw(f)` does the same, then redraws.
- In current tview, `Draw()` just queues a redraw. So "modify then call `Draw()`" still races; only the redraw is safe.

## Where tview deadlocks actually come from

Almost all of them come from one fact: **the event loop is a single goroutine, and it's the only thing that drains the update queue.** Anything that makes it wait on itself hangs the app.

1. **Calling `QueueUpdate`, `QueueUpdateDraw` or `Draw` from code already on the event loop.** That includes input handlers, `SetSelectedFunc`, `SetChangedFunc`, `SetDoneFunc`, `SetInputCapture` and the body of another `QueueUpdate`. You're pushing to a queue only you can drain. It may work while the buffer has room and then hang under load. Inside callbacks, just change the widgets directly; the loop redraws after handling the event.

2. **Blocking inside a handler on something that needs the UI.** For example, a key handler waits on a channel or `WaitGroup` while the background goroutine is stuck in `QueueUpdateDraw`, waiting for the loop the handler is blocking. Never do blocking I/O or waits in handlers. Start a goroutine and report back with `QueueUpdateDraw`.

3. **Calling `Application` methods from inside drawing code.** Custom `Draw` methods, `SetBeforeDrawFunc` and `SetAfterDrawFunc` run while the app holds its internal lock. Calling something like `app.GetFocus()` or `app.SetFocus()` there tries to take a mutex that isn't reentrant.

4. **Queueing when no loop is running.** Your poller can hit `QueueUpdateDraw` before `app.Run()` starts or after it returns. Once the buffer fills, the call blocks forever, which usually shows up as a hang on quit. Tie the poller to a `context` and cancel it before or when you call `app.Stop()`, as in the example above.

5. **Your own locks held across a queue call.** For example, the poller holds `mu` while calling `QueueUpdateDraw`, and a UI callback also takes `mu`. Copy the data out, release the lock, then queue the update.

**Rule of thumb:** background goroutines touch widgets only through `QueueUpdateDraw`. UI callbacks touch widgets directly and never block or queue. Nothing that runs during drawing calls back into `Application`.

Running with `go run -race` will catch the direct-mutation races quickly. For a real hang, a goroutine dump (`kill -QUIT <pid>`, or `Ctrl-\` if the terminal passes it through) usually shows the event loop blocked on a channel send or on the app mutex. That tells you which of the cases above you've hit.
