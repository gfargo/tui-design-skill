**Success and info messages: 3–5 seconds, then back to the idle status line. Errors and warnings: they stay until the user dismisses them, then move to a message log the user can reopen.** If a message disappears before anyone reads it, nobody can act on it. That's why the rule only bends for messages that are safe to miss.

### Rules

| Kind | Example | Lifetime | After |
|---|---|---|---|
| Success | `✓ Saved notes.txt` | Fades after 3–5 s, or sooner if new state replaces it | Goes to the log |
| Info / progress | `Connecting...` | Until the work finishes, then shows its result | Goes to the log |
| Warning | `! Low disk space` | Stays until dismissed | Goes to the log |
| Error | `✗ Save failed: permission denied` | Stays until dismissed (`Esc`) | Goes to the log |

**Errors in detail:**
- Say what failed and how to recover, and put the action key right next to it: `✗ Cannot connect to 10.0.0.4:6443 (connection refused)   r retry  l log  Esc dismiss`.
- Nothing should time an error out. Pressing `Esc` dismisses it, and after that it lives only in the log.
- If only one data source failed, show the error inline in that pane with a count and a retry key (`! prod-eu unreachable  2 of 3  r retry`). Don't blank the screen or turn it into a global status message.
- If you lose a connection, keep the last good data on screen, dimmed, with a `STALE 2m` / `reconnecting` marker. Don't flash an error and clear the view.

**Message log:**
- Write every message to the log, including errors and successes. Open it with `:messages` or a single key.
- Show the newest entry last. Give each entry a timestamp and its kind, and cap the log at about 200 entries per session.
- For long operations, the log entry is the receipt the user can come back to.

**Placement and styling:**
- Put messages in the status line, or in a toast at the bottom right just above the footer, so they never cover the row the user is working on. Show at most two at a time.
- Start each message with a symbol or label (`✓` / `!` / `✗`, or `Error:`) so its kind still reads under `NO_COLOR`. Color (green, yellow, red) should only reinforce the symbol. If the message already starts with `Error:`, don't add a symbol as well.

### At the floor sizes

```
80 cols │ ✗ Save failed: notes.txt is read-only        r retry ⋅ l log ⋅ Esc dismiss │
60 cols │ ✗ Save failed: notes.txt is read-only… ⋅ l log ⋅ Esc   │
```

When the line is too narrow, drop the less important hint keys first, then truncate the message with `…`. Always keep the `✗` and a way to dismiss and open the log, because the full text is still available in the log.

One more thing you'll probably run into: a "press again to confirm" prompt like `Press Ctrl+C again to quit` is a status message with its own timeout. It should last about 2 seconds, which is the window for the second press.

Full guidance is in `references/visual-patterns.md`, under the *Status / mode line* and *States* sections. If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink…), I can show how to implement the fade timer and the dismissible error in that framework.
