**Success and info messages: 3–5 seconds**, then clear back to the idle status line. **Errors and warnings: never auto-dismiss.** Keep them until the user dismisses them, then move them to a message log they can reopen. If a message disappears before the user reads it, they can't act on it.

### The rules

| Kind | Lifetime | Example |
|---|---|---|
| Success | Clears after 3–5 s or when the idle state returns | `✓ Saved notes.txt` |
| Info / progress | Clears after 3–5 s, or when the operation finishes | `Connecting...`, `3 files changed` |
| Warning | Stays until dismissed | `! Low disk space` |
| Error | Stays until dismissed, with recovery keys next to it | `✗ Cannot connect to 10.0.0.4:6443 (connection refused)  r retry  l view log  Esc dismiss` |

### What errors need

1. **Say what failed and how to recover.** Put the retry or escape key right beside the message (`r retry`, `Esc dismiss`). An error with no next step leaves the user stuck.
2. **Dismissing moves it to the log.** It doesn't delete it. Every message goes into a session log, successes included. Make the log reopenable with `:messages` or a dedicated key. List entries newest last, each with a timestamp and kind, and cap it at about 200 entries.
3. **Label the kind, not just the color.** Start each message with a symbol or word (`✓`, `!`, `✗`, or `Error:`) so it still reads correctly under `NO_COLOR`. Use green, yellow or red as one extra cue on top of that. Don't stack several cues: if the message already starts with `Error:`, it doesn't also need a `✗`.

### Where messages go

Use the status line, or a toast at the bottom-right just above the footer hint bar. Toasts there never cover the row the user is working on. Show **at most two toasts at once**.

```
┌ myapp ─ staging ─────────────────────────────────────────────┐
│ api-7d     1/1   4d                                          │
│ web-3f     1/1   2d                    ┌───────────────────┐ │
│                                        │ ✓ Saved notes.txt │ │
│                                        └───────────────────┘ │
│ ✗ Save failed: disk full   r retry ⋅ Esc dismiss             │  ← status line: sticky error
│ q quit ⋅ / filter ⋅ enter open ⋅ m messages ⋅ ? help         │  ← footer hints
└──────────────────────────────────────────────────────────────┘
```

At 60 columns, cut the error's detail text before you cut its recovery keys. `✗ Save failed  r retry ⋅ Esc` is still something the user can act on. The full text is waiting in the message log.

### Related timing
- **Spinners:** show one only after about 100–200 ms of work, so instant operations don't flash a spinner. Once a wait passes a second or two, show the elapsed time and offer `Esc` to cancel. Don't pick an automatic give-up timeout.
- **Ctrl+C confirmation:** if quitting would lose work, put `Press Ctrl+C again to quit` on the status line. A second press within about 2 s quits.

The skill's `references/visual-patterns.md` covers this under *Status / mode line* and *States*. If you tell me your framework (Bubble Tea, Ratatui, Textual, Ink), I can show how to wire the timer and the message log in it.
