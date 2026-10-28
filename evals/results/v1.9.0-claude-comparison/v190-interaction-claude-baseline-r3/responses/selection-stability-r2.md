The working directory is empty, so I can't see your code. This bug almost always has the same cause, though.

## The cause

You're storing the selection as a **row index**, such as `selected = 3`. Each refresh re-sorts the list, usually by CPU or memory, and processes start and exit. Index 3 now points to a different process, so the cursor stays on row 3 while the row's contents change under it.

## The fix: select by PID, not by position

Store the PID of the selected process. After each refresh, find which row that PID is on now.

```python
# state
selected_pid = None
scroll_offset = 0

def on_refresh(new_procs):
    global procs, selected_idx
    procs = sort(new_procs)

    # Find where the selected process ended up after the re-sort
    idx = next((i for i, p in enumerate(procs) if p.pid == selected_pid), None)

    if idx is None:
        # The process exited: stay at the same position (clamped) instead of jumping to the top
        idx = min(selected_idx, len(procs) - 1)
        selected_pid = procs[idx].pid if procs else None

    selected_idx = idx
    ensure_visible(selected_idx)   # adjust scroll_offset only if the row moved off-screen

def on_key_down():
    global selected_idx, selected_pid
    selected_idx = min(selected_idx + 1, len(procs) - 1)
    selected_pid = procs[selected_idx].pid   # key presses update the PID
```

The rule: **key presses change the PID, and refreshes recompute the index from the PID.**

## Related problems you may see next

1. **The viewport jumps.** When the selected process climbs from row 40 to row 2, the cursor follows it correctly, but the screen scrolls. Only change `scroll_offset` when the selected row leaves the visible area. Don't re-center it on every tick.
2. **The selected row moves while you're reading it.** Even with correct tracking, a process that re-sorts every second is hard to follow. Common fixes:
   - Pause sorting for a second or two after each key press. htop does something similar, and it feels natural.
   - Add a freeze key, like `top`'s pause or `Space`, that stops refreshing.
   - Add a "follow" toggle (htop's `F`) so the user can choose between keeping the cursor on the process or keeping it on the screen position.
3. **Reused PIDs.** For long-running tools, use `(pid, start_time)` as the key so a new process that gets an old PID isn't selected by mistake.
4. **Flicker.** Rebuild the data, then draw once. Don't clear the screen and redraw row by row. Most frameworks, like Bubble Tea, Ratatui, Textual, and Ink, already handle this if you update state and re-render once.

## Framework notes

- **Bubble Tea (`bubbles/table`)**: `SetRows` keeps the cursor *index*. After setting rows, look up the PID and call `SetCursor(idx)`.
- **Ratatui**: `TableState` stores an index. Recompute it with `state.select(Some(idx))` after each refresh.
- **Textual `DataTable`**: use row keys (`add_row(..., key=str(pid))`), then `move_cursor(row=table.get_row_index(key))`.

If you share your code or tell me which framework you're using, I can point to the exact lines to change.
