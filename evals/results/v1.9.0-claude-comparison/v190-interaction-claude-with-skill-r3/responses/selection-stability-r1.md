## Fix: track the selected process by PID, not by row index

The cursor jumps because you store the selection as a row number, like `selected = 7`. On each refresh the list gets rebuilt and re-sorted, so row 7 is now a different process. Store which process is selected and work out its row again after every refresh.

### 1. Store a stable ID and resolve it after each refresh

The PID is the natural key. PIDs get reused, so use `(pid, start_time)` if you can get the start time.

```python
# state
selected_key = None      # (pid, start_time); this is the source of truth
cursor_row = 0           # derived from selected_key on every refresh
scroll_offset = 0

def on_refresh(new_rows):
    old_rows = rows
    old_screen_pos = cursor_row - scroll_offset
    rows = apply_sort_and_filter(new_rows)

    idx = index_of(rows, selected_key)
    if idx is None:                          # the process exited
        idx = nearest_survivor(old_rows, rows, selected_key)
    cursor_row = idx
    selected_key = rows[idx].key if rows else None

    # Keep the highlight at the same screen position. Move the viewport, not the cursor.
    scroll_offset = clamp(cursor_row - old_screen_pos, 0, max(0, len(rows) - viewport_h))
```

Do this same re-resolve step after a sort change or a filter change, not only after a refresh.

### 2. When the selected process exits, pick a neighbor

Don't jump back to row 0. Select the next surviving row from the old ordering, or the previous one if there's no next. That way the user's place in the list survives a process dying.

### 3. Don't scroll the list under the cursor

If rows appear or disappear above the selection, adjust `scroll_offset` so the highlighted row stays where it was on screen (that's the last line of the code above). Only scroll when the selection would otherwise go off-screen.

### 4. Watch out for volatile sort keys

If the list is sorted by CPU% or memory, it will reorder every second. After you make the change above, the highlight stays on the same process, but that process moves around. Two things help:

- **Don't re-sort on every tick** unless the user picked that sort. Default to a calmer order, like PID or name.
- **Add a freeze key** and show it in the footer (htop uses `Z`). While frozen, don't reorder or insert rows. Show `PAUSED · 12 pending` in the header and apply the pending changes when the user resumes. This also makes it safe to aim a destructive action like `k` (kill) at a row.

### 5. Test it without a terminal

Write a unit test that selects PID 1234 at row 5, then feeds in a refresh where three new processes sort above it. Check that `selected_key` is still 1234 and that `cursor_row - scroll_offset` didn't change. Add a second test where 1234 disappears and check that its neighbor gets selected.

The rule behind all of this is that **the selection is part of your model, and the row index is just where it's drawn right now.** If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink…), I can show how to do this with its list or table widget. Some of them track the cursor by index internally, so you'd have to set it from your stored ID after each refresh.
