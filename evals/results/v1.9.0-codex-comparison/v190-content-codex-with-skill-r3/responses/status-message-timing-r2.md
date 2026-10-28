Use **3–5 seconds for success and informational messages** such as “Saved” or “3 files changed,” then return to the idle status line.

**Errors and warnings should stay until explicitly dismissed.** Include what failed and how to recover:

```text
Error: Save failed — permission denied
r retry | l view log | Esc dismiss
```

Keep every message in a reopenable history (`:messages` or a dedicated key), including after dismissal. Record timestamp, severity, and full text; roughly **200 entries per session** is a reasonable cap.

Use a severity word or symbol so meaning survives without color. `Error:` already supplies that cue; red can reinforce it.

At 80 columns and in a 60-column split, keep the failure and recovery action visible, shorten secondary details, and expose the full text in history. A single status line needs no extra border or duplicate severity markers.