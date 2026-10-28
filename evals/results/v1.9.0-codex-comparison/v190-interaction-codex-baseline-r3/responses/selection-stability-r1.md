Your TUI is likely tracking selection by **row index**. When the process list refreshes or reorders, that index points to a different process.

Track selection by a **stable process identity**, then find its new row after each refresh:

```text
selected = oldRows[selectedIndex].identity
newRows = fetchProcesses()
sort(newRows)

selectedIndex = findIndex(newRows, selected)
if selectedIndex == -1:
    selectedIndex = clamp(oldIndex, 0, len(newRows) - 1)
```

For processes, use **PID + process start time** as the identity, since PIDs can be reused.

Also:

- Use a deterministic sort, with identity as a tie-breaker.
- Update the existing table instead of recreating it each second.
- Preserve the scroll offset, adjusting only enough to keep selection visible.
- If the list is empty, clear selection safely.

If you share your refresh code and TUI framework, I can show the exact fix.