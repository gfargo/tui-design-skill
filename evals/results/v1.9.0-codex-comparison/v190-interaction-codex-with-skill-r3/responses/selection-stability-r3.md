**Track the selected process by identity, then restore its position after each refresh.** Keeping only a row index means “row 7” can become a different process whenever rows reorder.

Use this refresh policy:

- **Stable identity:** store `(PID, start time)` so PID reuse cannot select a different process. Re-resolve that identity after refresh, sorting, and filtering.
- **Stable viewport:** remember the selected row’s screen offset. Adjust the scroll offset to keep it there, clamping at list boundaries.
- **Predictable removal:** if the process exits, select its next surviving neighbor from the old order, otherwise the previous one. If none remain, clear selection.
- **Controlled sorting:** update CPU/memory values without automatically re-sorting every second. Make continuous CPU sorting an explicit mode; even then, keep selection attached to the process.
- **Pause control:** offer a visible freeze key, such as `p pause`. While paused, stop reorders and appends, display `PAUSED · N pending`, and apply pending changes on resume.

Keep this state outside the rendering function; rebuilding the table must not reset selection or scrolling.

Verify with four cases: a row inserts above selection, CPU rankings swap, the selected process exits, and the list becomes empty. In each case, selection and viewport should follow the policy above.