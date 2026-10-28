The cursor jumps because your selection is stored as a **row index**. Each refresh rebuilds the list, so if processes start or exit above row 7, or the CPU% sort reorders things, index 7 now points at a different process. The fix is to store the selection as the **PID** and work out its row again after every refresh.

### 1. Track the selection by ID, not by index

```python
# state
selected_pid: int | None
scroll_offset: int          # first visible row

def on_refresh(new_rows):
    old_rows = self.rows
    old_screen_pos = index_of(old_rows, selected_pid) - scroll_offset

    self.rows = new_rows    # apply the same sort/filter as before

    idx = index_of(new_rows, selected_pid)
    if idx is None:                       # the process exited
        idx = nearest_survivor(old_rows, new_rows, selected_pid)
        selected_pid = new_rows[idx].pid if new_rows else None

    # keep the selected row at the same screen position
    scroll_offset = clamp(idx - old_screen_pos, 0, max_offset)
```

Recompute the row from the ID after every **refresh, sort, and filter**, not only after the timer tick.

### 2. When the selected process exits, pick its neighbor
If the PID is gone, select the next row that still exists, or the previous one if it was last. Don't reset to row 0. Jumping to the top is the most disorienting thing that can happen here.

### 3. Don't scroll the list under the cursor
When rows are added or removed above the selection, adjust `scroll_offset` so the selected row stays at the same screen line (that's the `old_screen_pos` step above). Only move the viewport when the selection would otherwise go off screen.

### 4. Don't re-sort on every refresh unless the user chose that sort
If the list is sorted by CPU% or memory, rows reorder every second on purpose. Even with ID tracking, the highlighted row will move around the screen as the process climbs or drops. Two options:
- Default to a stable sort key such as PID or name, and make volatile sorts something the user picks.
- Or accept the reordering, but keep the highlight on the same process using step 1.

### 5. Add a freeze key
Do what htop does with `Z` and give users a key that pauses updates while they read or act on a row:
- Show it in the footer hints, e.g. `Z freeze`.
- While frozen, stop all reordering and new rows, and show `PAUSED · 12 pending` in the header.
- Apply the pending changes when the user unfreezes.

This matters most before destructive actions. Someone about to press `k` to kill a process must not have the row change under them. As an extra safeguard, the kill confirmation should name the process (`Kill 4182 node?`), not just the row.

### Two related checks
- **Keep the poll off the UI thread.** Read the process data in a background task or command and send the result back as a message. If the UI blocks during the read, input lags and redraws stutter, which can look like the cursor jumping.
- **Test it without a terminal.** Feed two snapshots into your update logic, one where a row above the selection disappears and one where the selected PID disappears. Check that `selected_pid` and the selected row's screen position come out as expected.

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink, …), I can map this onto its list or table widget. Most of them track selection by index internally, so you'd keep the PID in your own state and set the widget's cursor from it after each update.
