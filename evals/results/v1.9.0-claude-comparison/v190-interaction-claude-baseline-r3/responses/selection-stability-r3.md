I couldn't find any files in the working directory, so I can't see your code. This bug almost always has the same cause, though, and the fix doesn't depend on the framework.

## The cause

Your cursor is stored as a **row index**, like `selected = 3`. Every refresh rebuilds the list. Processes start and exit, and the list gets re-sorted by CPU or memory. Row 3 then holds a different process, so the cursor appears to jump.

## The fix: track the selection by PID, not by row number

Store the PID of the selected process. After each refresh, look up which row that PID is now on and move the cursor there.

```python
# State
selected_pid = None
cursor = 0

def on_refresh(new_procs):
    global cursor, selected_pid
    procs = sort_stable(new_procs)          # see "Stable sorting" below

    if selected_pid is not None:
        idx = next((i for i, p in enumerate(procs) if p.pid == selected_pid), None)
        if idx is not None:
            cursor = idx                     # the process moved: follow it
        else:
            cursor = min(cursor, len(procs) - 1)   # the process exited: stay near the same spot
            selected_pid = procs[cursor].pid if procs else None
    else:
        cursor = min(cursor, max(len(procs) - 1, 0))

    render(procs)

def on_key(key, procs):
    global cursor, selected_pid
    if key == "down": cursor = min(cursor + 1, len(procs) - 1)
    if key == "up":   cursor = max(cursor - 1, 0)
    selected_pid = procs[cursor].pid         # update the PID on every user move
```

## Related fixes you'll probably need

1. **Stable sorting.** If two processes both show 0.0% CPU, an unstable sort can swap them on every refresh. Add a tiebreaker:
   ```python
   procs.sort(key=lambda p: (-p.cpu, p.pid))
   ```

2. **Keep the scroll position steady.** If your list scrolls, store the scroll offset separately. Only change it when the cursor would go off-screen. Don't recalculate it from scratch on every refresh, or the view will shift even when the cursor stays put.

3. **Decide what the cursor should do when a process moves.** There are two reasonable choices:
   - **Follow the process** (what the code above does): the highlighted row moves when its process re-sorts.
   - **Stay on the same screen row**: the highlight stays still and a different process moves under it.

   `htop` follows the process. A common middle ground is to pause re-sorting while the user is pressing navigation keys, or to add a "freeze" key like `F` or space.

4. **Handle exited processes.** If the selected PID disappears, clamp the cursor to the nearest valid row (shown above). Don't reset it to 0.

## Framework-specific notes

- **Bubble Tea (Go):** in your `tickMsg` handler, don't swap in `table.SetRows(...)` and leave the cursor alone. Find the selected PID's new index and call `m.table.SetCursor(idx)`.
- **Textual (Python):** in `DataTable`, use the PID as the row key: `add_row(..., key=str(pid))`. Read the current key before you `clear()`. After repopulating, call `move_cursor(row=table.get_row_index(key))`. Better still, update cells in place with `update_cell` instead of clearing.
- **Ratatui (Rust):** after rebuilding the `Vec`, call `TableState::select(Some(new_idx))`. Also keep the `TableState` between frames rather than creating a new one each time, so `offset` is preserved.

If you share your refresh and render code, or tell me which framework you're using, I can point to the exact lines to change.
