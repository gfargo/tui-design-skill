The cursor jumps because it's stored as a **row index**. Each refresh rebuilds the list, a different process ends up at row 7, and your cursor now points at that one. To fix it, **track the selection by the process's PID** and work out its row again after every refresh.

## The fix

```text
state:
  selectedPID     // the source of truth
  cursorRow       // derived, never stored across refreshes
  viewportTop     // first visible row

on refresh(newRows):
  oldRows   = rows
  oldScreen = cursorRow - viewportTop        // where the cursor sits on screen
  rows      = newRows                        // apply filter/sort as usual

  i = indexOf(rows, pid == selectedPID)
  if i == -1:                                // the process exited
    i = nearestSurvivor(oldRows, rows, selectedPID)
    selectedPID = rows[i].pid
  cursorRow = i

  // keep the selected row at the same screen position
  viewportTop = clamp(cursorRow - oldScreen, 0, max(0, len(rows) - height))

on key ↑/↓:
  cursorRow = clamp(cursorRow ± 1)
  selectedPID = rows[cursorRow].pid          // update the ID whenever the user moves
```

`nearestSurvivor` walks forward from the old position in `oldRows` and picks the first PID that still exists in `rows`. If none is found, it walks backward. Don't reset to row 0. When the process you were on exits, the cursor should land on its neighbour.

## Other causes of the same jump

1. **Sorting by a fast-changing column.** If the list is sorted by CPU% or memory, rows reorder every second by design. With PID tracking the cursor stays on your process, but that process moves around the screen. Options:
   - Only re-sort when the user changes the sort. Between sorts, update the values in place and leave the order alone.
   - Or accept the reordering and rely on the viewport anchoring above. The selected row then stays put on screen while the other rows move around it.
2. **The view scrolling under the cursor.** When processes appear or exit above the selection, a viewport fixed to an index offset makes everything shift. The `viewportTop` line above fixes this. Only move the viewport when the selection would otherwise go off-screen.
3. **No pause key.** Add one, like htop's `Z`, and show it in the footer. While paused:
   - stop reordering and adding rows;
   - show `PAUSED` in the header, with a count of pending changes;
   - apply everything when the user resumes.

   This matters most when someone is about to kill a process and needs the row to stay put.

## Smaller points

- If you also have a filter or search, run the same "find the PID again" step after it changes, not just after the timer fires.
- PIDs can be reused once a process exits. If that matters, say before sending a signal, use `(pid, start_time)` as the key.
- Fetch the process data off the UI thread, deliver it as a message or event, and redraw only when it arrives. A 1-second blocking `ps` call inside the render loop causes its own stutter.
- Write a unit test without a terminal: put the cursor on PID 300, feed in a refresh where rows above it vanish and the order changes, and check that `selectedPID == 300` and the cursor's on-screen row hasn't moved. Then add a refresh where PID 300 exits, and check that the cursor lands on its neighbour.

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink, …), I can show how this fits its list or table widget. Some of them, like the Bubbles table and Ratatui's `TableState`, store only an index, so you have to keep the PID mapping yourself.
