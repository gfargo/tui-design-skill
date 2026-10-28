Track selection by **process identity, not row number**. On refresh, sorting or new processes can move rows, so keeping “row 7” selected can highlight a different process.

For each refresh:

1. Save the selected process’s identity—ideally `(PID, start_time)`, since PIDs can be reused.
2. Fetch and sort the new process list.
3. Find that identity in the new list and update the selected row.
4. If it exited, select the nearest valid row.
5. Preserve the scroll offset, adjusting only enough to keep the selection visible.

```text
selected_id = identity(rows[selected_index])
old_index = selected_index

rows = fetch_and_sort_processes()

selected_index = find_index(rows, selected_id)
if selected_index is missing:
    selected_index = clamp(old_index, rows)
```

Use a deterministic tie-breaker such as PID when sorting. If you sort by CPU usage, rows will still move every second; a fixed sort or temporarily freezing sorting during navigation can make browsing easier.

Also avoid recreating the table’s selection and scroll state on every render. Your workspace appears empty, so I couldn’t inspect the implementation; share the refresh and selection code for a precise patch.