The cursor is probably tied to a **row index**, while refreshes reorder the processes. Keep selection tied to a **process identity** instead.

On each refresh:

1. Save the selected process’s identity—ideally `(PID, start time)`, since PIDs can be reused.
2. Update and sort the process list.
3. Find that process in the new list and select its new row.
4. If it exited, select the nearest valid row.

```text
selected_id = identity(rows[selected_index])
previous_index = selected_index

rows = refresh_and_sort()

selected_index = find_index(rows, selected_id)
if selected_index is missing:
    selected_index = clamp(previous_index, 0, len(rows) - 1)
```

Handle an empty list with no selection. Also use a deterministic tie-breaker when sorting, such as PID, and preserve the scroll offset unless the selected process moves outside the viewport.

If your framework supports keyed rows, use the process identity as the row key too.