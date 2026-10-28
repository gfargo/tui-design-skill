**Rule:** each Esc press does the innermost thing that applies, once, and Esc never quits. `q` goes back one level and only quits at the root. `Ctrl+C` cancels running work if there is any, and otherwise quits from anywhere.

### Esc: one step per press, innermost first

| # | When this is true | Esc does |
|---|---|---|
| 1. Cancel | A request, load, or long action is running | Cancels it and keeps the old data on screen |
| 2. Close | A modal, menu, palette, help screen, or completion popup is open | Closes **only the top one** |
| 3. Clear | A filter, search, or multi-selection is active | Clears it. A cancelled search goes back to where the cursor was before |
| 4. Back | You're in a drill-down, a detail view, or a focus trap | Goes back **one** level |
| 5. Root | None of the above | **Does nothing.** Esc never quits |

Your five Esc jobs probably map onto these five rows. The ordering is what gives them a fixed sequence. Check top to bottom, run the first match, and stop. Each press does one step only, so a user can always predict what the next press will do.

### q: back one level, quit only at the root

Your current "q quits from anywhere" is the part to change. In a nested app, a user who presses `q` three levels deep wants to go back, not lose all their context. So:

- **Nested view:** `q` goes back one level, like step 4 of the Esc ladder.
- **Root:** `q` quits.
- **Text field has focus:** `q` is just the letter q. Never let a binding take over typed input.
- (In a single-view app, `q` would quit straight away. Yours is nested, so the rules above apply.)

### Ctrl+C: the emergency exit

- **Something is running:** the first press cancels it, the same as Esc step 1.
- **Nothing is running:** it quits from **anywhere**, without stepping back through the levels. This is the reserved-key behavior users expect, and it's the guaranteed way out.
- **Quitting would lose something:** the first press puts `Press Ctrl+C again to quit` on the status line. A second press within about 2 seconds quits.

### Confirming a quit

- Only ask when quitting loses something, like unsaved edits or jobs that can't resume: `Quit? 2 jobs are still running [y/N]`, with No as the default.
- An idle quit never asks.
- Every quit path runs **the same teardown**: restoring raw mode, cursor, mouse capture, and the alternate screen. That includes root `q`, a confirmed `q`, and the second `Ctrl+C`.

### Dispatch sketch

```
on Esc:
  if op.running        -> op.cancel()           ; return
  if overlays.any      -> overlays.pop()        ; return
  if filter/search/sel -> clear()               ; return   // restore pre-search cursor
  if stack.depth > 1   -> stack.pop()           ; return
  // root: no-op

on q:
  if textInput.focused -> insert('q')           ; return
  if stack.depth > 1   -> stack.pop()           ; return
  requestQuit()

on Ctrl+C:
  if op.running        -> op.cancel()           ; return
  if wouldLoseWork && !armedWithin(2s) -> arm(); status("Press Ctrl+C again to quit"); return
  quit()                                         // same teardown as every other path
```

Two practical notes:

- **Esc can be slow to arrive.** A lone Esc is ambiguous with the start of an Alt key sequence, so tmux holds it for `escape-time` before passing it on (500 ms before tmux 3.5). Don't make anything depend on Esc being fast, and test inside tmux.
- **Show the current Esc/q action in the footer.** If the hint updates with context (`esc clear filter`, `esc back`, `q quit`), users can see which step comes next instead of guessing.
