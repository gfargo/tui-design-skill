Use **3–5 seconds for success and informational messages**. **Errors and warnings should stay until explicitly dismissed**, with a clear recovery action.

| Message kind | Behavior |
|---|---|
| Success / info | Show for 3–5 seconds, then restore the idle status line. |
| Warning / error | Keep visible until dismissed; offer actions such as retry, view details, or dismiss. |

Write **every message** to a reopenable history, such as `:messages`: timestamp, kind, newest last, capped around 200 session entries. Dismissing an error removes it from the status line but preserves it in history.

Use text labels so meaning survives `NO_COLOR`: `Error: Save failed — disk full`. Avoid adding both a label and redundant symbols.

Keep the status line borderless and compact. At both 80×24 and 60 columns, preserve the failure summary and recovery keys; put long details in the message log:

```text
Wide: Error: Save failed — disk full   r retry   l log   Esc dismiss
60c:  Error: Disk full | r retry | l log | Esc dismiss
```

If using toasts instead, show at most two, positioned above the footer without covering the active row.