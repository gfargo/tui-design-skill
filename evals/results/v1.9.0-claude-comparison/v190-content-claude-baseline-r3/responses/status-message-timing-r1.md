The working directory is empty, so I can't see your code. Here's general guidance you can adapt.

## How long messages stay up

Base the duration on severity and length:

| Kind | Behavior | Typical duration |
|---|---|---|
| **Info / success** ("Saved", "Copied 3 items") | Disappears on its own | **2–4 s**, or about 1 s + 60 ms per character, capped around 5 s |
| **Warning** ("File changed on disk") | Disappears on its own, but more slowly | **5–8 s** |
| **Error** | **Stays** until the user acts (see below) | Doesn't time out |
| **Progress** ("Indexing… 42%") | Stays while the work runs, then is replaced by the result | Lasts as long as the operation |

A few rules make timed messages feel right:
- **Reset the timer when a new message arrives.** Don't stack messages in a single-line status bar. A new message replaces the old one, unless the old one is an error (see below).
- **Clear early on input when it makes sense.** For info messages, the next keypress that changes state can clear them. Don't clear on every keystroke, though, or people will miss the message.
- **Keep messages up while the user is away.** If you can detect idle time or lost focus, pause the timer.
- **Use a single redraw tick** (for example, 100–250 ms) to check expiry. Don't create a timer per message.

## What to do with errors

1. **Keep them on screen.** An error stays until the user dismisses it (Esc, or any key), retries, or fixes the cause. Errors are the messages people most need to read, and they often show up while the user is looking somewhere else.
2. **Don't let lower-severity messages overwrite them.** A later "Saved" shouldn't silently replace "Failed to write config.toml". Either queue the info message, or show it and keep an error marker visible (e.g. `[1 error]`).
3. **Write every error to a log.** Keep a message history the user can open with a key (`:messages`, a log pane, or similar), and include a timestamp, severity, and full detail. The status line only has room for a one-line summary. Vim, Helix and lazygit all do some version of this.
4. **Make them easy to spot without relying on color alone.** Use a color plus a prefix such as `E:` or `✗`. Some users run monochrome terminals or have color vision deficiencies, and screen readers ignore color.
5. **Tell the user what to do.** "Permission denied: ~/.config/app.toml — press r to retry, ? for details" beats "Error 13".
6. **Use a modal or popup only for errors that block work.** Data loss risk or a dead connection justifies interrupting the user. Everything else belongs in the status line plus the log.

## A minimal model

```text
StatusMessage { text, severity, created_at, sticky }
- sticky = (severity == Error)
- on tick: if !sticky && now - created_at > ttl(severity, text) → clear
- on new message: if current is sticky && new.severity < Error → push to log, show error-count badge
- on dismiss key: clear sticky message
- every message → append to history log
```

If you share your framework (Bubble Tea, Ratatui, Textual, Ink, etc.) or your code, I can sketch a concrete implementation.
