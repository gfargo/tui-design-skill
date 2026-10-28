Use **3–5 seconds for success and informational messages**. Keep **errors and warnings visible until explicitly dismissed**.

| Message kind | Behavior |
|---|---|
| Success / info | Show for 3–5 seconds, then return to idle status. |
| In progress | Remain until the operation completes, fails, or is canceled. |
| Warning / error | Stay until dismissed; include a recovery action. |

Write **every message to a reopenable message log immediately**, including errors. Use timestamps and severity, newest last, and cap it around 200 entries per session. Dismissing an error clears its display; its history remains available through `:messages` or a documented key.

An error should say what failed and what to do next:

```text
Wide:    Error: Save failed: permission denied.  r retry  l log  Esc dismiss
60 cols: Error: Save failed.  r retry  l log  Esc dismiss
```

At 80×24 and 60 columns, keep the recovery keys visible; put longer details in the log. Use one text label plus optional color—`Error:` already communicates severity, so extra icons and borders add clutter. Don’t let a routine “Saved” notification overwrite an undismissed error.