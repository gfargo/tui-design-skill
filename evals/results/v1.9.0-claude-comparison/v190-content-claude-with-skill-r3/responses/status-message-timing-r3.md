**Short version:** success and info messages fade after 3–5 seconds. Errors and warnings stay on screen until the user dismisses them, then move to a message log they can reopen.

### Timing by message kind

| Kind | Example | How long it stays |
|---|---|---|
| Success | `✓ Saved notes.txt` | Fades after 3–5 s, or gives way to the idle state |
| Info | `Connecting...`, `3 files changed` | Same, 3–5 s |
| Warning | `! Low disk space` | Stays until dismissed |
| Error | `✗ Save failed` | Stays until dismissed |

The reason for the split is that a message that disappears before anyone reads it can't be acted on. Losing a "Saved" confirmation costs little. Losing an error means the user doesn't know something failed.

### What an error should look like

Say what failed and how to recover, and put the recovery keys right next to it:

```
✗ Cannot connect to 10.0.0.4:6443 (connection refused)
  r retry   l view log   Esc dismiss
```

- **Lead with a symbol or label word** (`✓`, `!`, `✗`, or `Error:`) so the kind still reads under `NO_COLOR`. Add green, yellow or red on top, but never rely on color alone. If the message already starts with `Error:`, you don't need the `✗` as well.
- **When dismissed, move it to the message log** instead of throwing it away.

### The message log

- Write **every** message to the log, not just errors.
- Reopen it with a command or key (`:messages`, or something like `l`).
- Show newest last, with a timestamp and kind on each entry.
- Cap it at around 200 entries per session.

### If you use toasts instead of the status line

- Put them at the bottom-right, just above the footer hint bar, so they never cover the row the user is working on.
- Show at most two at a time.
- The same rules apply: success and info fade, errors stick, everything goes to the log.

### Related details

- **Long operations:** a short success message isn't enough on its own. Also leave a receipt in scrollback or the message log.
- **Double-press confirmations:** for a hint like `Press Ctrl+C again to quit`, the time limit is how long the second press counts (about 2 seconds), not a fade timer.

All of this comes from the skill's `references/visual-patterns.md`, mainly the *Status / mode line* section (line 460) and the *States* section (lines 552–569).
