The working directory is empty, so I can't see your code. This bug almost always has the same cause, though, and the fix doesn't depend much on which framework you use.

## Why it happens

The cursor is stored as a **row index**, like `selected = 3`. On each refresh the list gets re-sorted (by CPU, memory, etc.) and processes start or exit, so a different process ends up at index 3. The cursor stays on the row number while the process you picked moves somewhere else.

## The fix: remember the process, not the row

Store the selected process's **PID**, which stays the same between refreshes. After each refresh, find where that PID ended up and put the cursor there.

```python
# state
selected_pid = None
cursor = 0
scroll_offset = 0

def on_refresh(new_procs):
    global procs, cursor, selected_pid
    old_cursor = cursor
    procs = new_procs

    # 1. Find the selected process in the new list
    idx = next((i for i, p in enumerate(procs) if p.pid == selected_pid), None)

    if idx is not None:
        cursor = idx
    else:
        # 2. The process exited: stay near the same spot instead of jumping to the top
        cursor = min(old_cursor, len(procs) - 1) if procs else 0
        selected_pid = procs[cursor].pid if procs else None

    keep_cursor_visible()

def on_key(key):
    global cursor, selected_pid
    if key == "down": cursor = min(cursor + 1, len(procs) - 1)
    if key == "up":   cursor = max(cursor - 1, 0)
    selected_pid = procs[cursor].pid   # update the PID whenever the user moves
    keep_cursor_visible()
```

## Related fixes that make it feel stable

1. **Make the sort stable.** When two processes tie (say both at 0.0% CPU), break the tie with PID, e.g. `key=(-p.cpu, p.pid)`. Otherwise tied rows swap places on every refresh, which looks like flicker even when the cursor logic is right.
2. **Don't reset the scroll position on refresh.** Only scroll when the cursor would go off-screen:
   ```python
   def keep_cursor_visible():
       global scroll_offset
       if cursor < scroll_offset: scroll_offset = cursor
       elif cursor >= scroll_offset + view_height: scroll_offset = cursor - view_height + 1
   ```
   Many widgets lose their scroll position when you replace their whole item list. If yours does, update rows in place or save and restore the offset yourself.
3. **Optional: let the cursor follow the process or stay on the row.** htop lets you choose (`F` toggles "follow"). Following the process is the better default. Some users prefer that a row they're about to act on stays put.
4. **Optional: pause re-sorting while the user is navigating.** For example, skip the sort for ~1–2 s after a keypress, or add a freeze key like `Space`. That way the row under the cursor doesn't move just as someone presses `k` to kill it.
5. **Make destructive actions use the PID.** When the user kills or renices a process, act on `selected_pid` and not `procs[cursor]`. Otherwise a refresh between the keypress and the action could hit the wrong process. It's also worth showing the PID in the confirmation prompt.

## Framework notes

- **Bubble Tea (Go):** store `selectedPID` in your model. In the `tickMsg` handler, rebuild the rows, then call `table.SetCursor(idx)`.
- **Textual (Python):** use `DataTable` with `key=str(pid)` on each row. After a refresh, call `move_cursor(row=table.get_row_index(key))`.
- **Ratatui (Rust):** keep `selected_pid: Option<u32>`. After a refresh, call `table_state.select(procs.iter().position(|p| p.pid == pid))`. Reuse the same `TableState` so the scroll offset carries over.

If you share the refresh and rendering code, I can point to the exact lines to change.
