**Anchor selection to a process identity, not a row number.** If you preserve “row 7” across refreshes, sorting or inserted rows can put a different process under the cursor.

On each refresh:

1. Remember the selected process key—prefer `(PID, start time)`, since PIDs can be reused.
2. Update the data, then find that key in the visible list again.
3. Preserve its screen position by adjusting the viewport offset when rows above it change.
4. If it disappeared, select the next surviving neighbor from the old order, otherwise the previous. Clear selection if the list is empty.

Also check your sorting: **updating CPU values doesn’t require reordering rows every second.** Keep the existing order until the user requests a sort. If continuous CPU ranking is intentional, make it an explicit live-sort mode and keep selection attached to the same process.

Offer a visible freeze shortcut, for example `p pause`. While paused, hold the displayed snapshot, show `PAUSED · 12 pending changes`, and apply the latest snapshot on resume.

Verify with four cases: insertion above selection, selected process exiting, CPU rankings changing, and PID reuse. The selected process and its screen position should remain steady whenever it survives.