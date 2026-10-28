Make Esc follow one fixed ladder, stop `q` from quitting outside the root, and let Ctrl+C be the one key that quits from anywhere.

## Esc: each press does the innermost step that applies, once

| Step | Applies when | Esc does |
|---|---|---|
| 1. Cancel | A request, load, or long action is running | Cancels it and keeps the old data |
| 2. Close | A modal, menu, palette, help screen, or completion popup is open | Closes only the top one |
| 3. Clear | A filter, search, or multi-selection is active | Clears it. A cancelled search jumps back to where the cursor was before the search |
| 4. Go back | A drill-down, detail view, or focus trap is open | Goes back one level |
| 5. Root | None of the above | Nothing. **Esc never quits** |

One press does one step. If a popup is open over a filtered list in a detail view, it takes three presses to get back out. Users can predict that, and they never fall out of the app by accident.

## q: goes back in nested views and quits only at the root

- Your current "q quits from anywhere" is the part to change. In a nested view, `q` should go back one level, like Esc step 4. At the root, it quits.
- While a text field has focus, `q` is just the letter q. This is the most common bug with single-letter quit keys.
- Exception: in an app with only one view, `q` can just quit.

## Ctrl+C: cancels running work first, then quits from anywhere

- If something is running, Ctrl+C cancels it, like Esc step 1.
- If nothing is running, it quits from any depth without stepping back through the levels. This is the escape hatch users expect at the terminal level.
- If quitting would lose something, the first press shows `Press Ctrl+C again to quit` on the status line. A second press within about 2 seconds quits.

## Confirm only when quitting would lose something

- Unsaved edits, or running work that can't be resumed: `Quit? 2 jobs are still running [y/N]`, with No as the default.
- An idle quit never asks for confirmation.

## Two implementation rules

1. **Every quit path runs the same teardown.** That covers `q` at the root, a confirmed quit, and the second Ctrl+C. Each one must restore raw mode, the cursor, mouse capture and the alternate screen. If you have separate exit paths, this is where terminals get left broken.
2. **Don't make a single Esc press time-sensitive.** A terminal can't immediately tell a lone Esc from the start of an Alt+key sequence. tmux waits `escape-time` to decide: 500 ms by default before tmux 3.5, 10 ms since. Test the ladder inside tmux. Don't bind Ctrl+[ separately, because it sends the same byte as Esc.

## Code shape

Make this one function that checks the steps in order. Don't scatter Esc handlers across views:

```
on Esc:
  if op.running        -> op.cancel()
  elif overlays        -> overlays.pop()
  elif filter/search/selection active -> clear it (restore position)
  elif stack.depth > 1 -> stack.pop()
  else                 -> no-op

on q:
  if textInputFocused  -> insert 'q'
  elif stack.depth > 1 -> stack.pop()
  else                 -> requestQuit()      # confirms only if work would be lost

on Ctrl+C:
  if op.running        -> op.cancel()
  elif hasUnsaved and not armed -> arm(2s), show "Press Ctrl+C again to quit"
  else                 -> quit()             # same teardown as every other path
```

Because the ladder is a pure function of state, you can unit-test it without a terminal. Build each state, send a synthetic Esc, `q` or Ctrl+C, and check which single step happened. Also list the ladder in your `?` help screen so the five Esc behaviors are documented instead of something users have to discover.
