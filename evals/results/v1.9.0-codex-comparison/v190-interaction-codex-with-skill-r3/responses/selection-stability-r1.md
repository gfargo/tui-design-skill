Keep the selection attached to a **process identity**, rather than its row number. The likely cause is that each refresh changes row order while the selected index stays the same.

On every refresh:

1. Remember the selected process’s ID and its position within the viewport. Use **PID + process start time**, since PIDs can be reused.
2. Update the process data, then find that same ID in the visible list.
3. Adjust the viewport offset so the selected process stays on the same screen line where possible.
4. If it exited, select the next surviving neighbor from the previous ordering, falling back to the previous neighbor. If the list is empty, clear selection.

Also check your sorting policy. Sorting by CPU usage every second will keep moving rows even with correct selection tracking. Update metrics in place and preserve ordering until the user requests a sort; if continuous ranking is intentional, offer a visible pause control such as `p Pause`.

Test refreshes that reorder rows, insert or remove processes above the selection, remove the selected process, and reuse a PID. **Both process identity and screen position should remain stable whenever possible.**