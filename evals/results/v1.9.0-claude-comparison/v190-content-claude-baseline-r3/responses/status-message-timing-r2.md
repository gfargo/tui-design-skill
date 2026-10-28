I didn't find any files in the working directory, so this is general guidance rather than advice based on your code.

## How long messages should stay

- **Info and success messages** ("Saved", "Copied 3 items"): about **2–4 seconds**, then clear on their own. A good rule is roughly 1s base + ~60ms per word, capped near 5s.
- **Warnings**: a bit longer, about **5–8s**. Also clear them as soon as the user acts (on the next keypress) so they don't hang around.
- **Progress or ongoing state** ("Syncing…"): no timer. Keep it up until the operation finishes, then replace it with the result.
- **A new message replaces the old one** and restarts the timer. Don't queue them. If several things happen at once, combine them ("3 files saved") so the line doesn't flicker.
- **Reset the timer when the terminal is resized or the app is redrawn**, so a message isn't lost before anyone sees it.

## What should happen to errors

1. **Errors should not clear on a timer.** If the user looks away, a disappearing error is lost. Keep it until one of these happens:
   - the user dismisses it (Esc, or any key you choose),
   - the user retries the failed action and it works,
   - a more important error replaces it.
2. **Make errors look different**: red or inverse colors plus a marker like `✗` or `E:`, so they're still clear without color (`NO_COLOR`, colorblind users).
3. **Keep them short and actionable**: what failed and what to do next, e.g. `✗ Write failed: permission denied — :w! to force`. Truncate long errors with a hint like `(? for details)`.
4. **Keep a message history.** Save every status message, especially errors, in a scrollback buffer the user can open (like Vim's `:messages` or a `?`/`!` key). That way, clearing the status line never loses information.
5. **Log errors to a file** when there's a debug/log mode. A status line is no place for stack traces.
6. **Fatal errors** (where the app can't continue) shouldn't use the status line at all. Show a modal or a clean exit with the message printed to stderr after the terminal is restored.

## Summary

| Type | Clears after | Clears early on |
|---|---|---|
| Info / success | 2–4s | next message |
| Warning | 5–8s | next keypress / message |
| Progress | never (on its own) | completion |
| Error | never (on its own) | dismiss, successful retry, newer error |
| Fatal | n/a: modal or exit | n/a |

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink, etc.), I can sketch how to build this, e.g. a timer that emits a clear-message event plus a message history.
