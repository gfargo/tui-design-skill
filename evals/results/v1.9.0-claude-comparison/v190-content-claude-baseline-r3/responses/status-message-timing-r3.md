The working directory is empty, so I can't see your TUI's code. These are general guidelines you can adapt.

## How long messages stay up

Base the time on how long the message is and how much it matters:

| Message type | Duration | Notes |
|---|---|---|
| **Success / info** ("Saved", "Copied 3 items") | ~2–4 s | Short confirmations. About 3 s is a good default. |
| **Longer info** | ~1 s base + ~60 ms per character, capped at 6–8 s | Gives people time to read longer text. |
| **Warnings** | 5–8 s, or until the next keypress | Make sure they get noticed. |
| **Progress** ("Indexing… 42%") | Until the operation finishes | Then replace it with the result message. |
| **Errors** | **Until the user dismisses them** (see below) | Don't let them disappear on a timer. |

Other rules worth following:
- **A new message replaces the old one at once.** Don't queue several messages to show one after another, because then the status line falls behind what's actually happening.
- **Pick one way messages clear.** Either a timer, or "clears on the next keypress" (vim-style), which works well in keyboard-driven TUIs. Mixing the two confuses people.
- **Don't let an error be hidden by a minor message.** A "Saved" from a later action shouldn't wipe out an earlier failure the user hasn't seen yet. Give messages priorities so lower ones can't overwrite higher ones until those are acknowledged.
- **Keep the status line the same height.** Truncate long text with `…` so the layout doesn't jump around.

## What to do with errors

1. **Keep them until acknowledged.** Clear an error on Esc, on any keypress, or when the user starts a new action that addresses it. Never use a timer. If the user glanced away, the error is lost.
2. **Make them look different without relying on color alone.** Use red or inverse video plus a prefix like `✗`, `E:`, or `Error:`, since some people use monochrome terminals or are colorblind.
3. **Say what to do next.** Write `Error: config.toml line 12: expected '='. Press e to edit`, not just `Parse error`.
4. **Save them to a log.** Write every error, with a timestamp, to an in-app message history (like vim's `:messages`) and/or a log file. The status line is a notification, not the record. Show a hint like `(2 more, press ! to view)` when several errors stack up.
5. **Don't put long or multi-line errors in the status line.** Show a truncated summary there and open the full text in a popup or pane when the user asks.
6. **Keep fatal errors separate.** If the app has to exit, restore the terminal first (leave the alternate screen, reset raw mode), then print the error to stderr so it stays visible in the shell afterward.

## A simple model to implement

```
Message { text, level: Info|Warn|Error|Progress, created_at, sticky: bool }
```
- `sticky = (level == Error)`
- On each render tick, clear it if it's not sticky and `now - created_at > ttl(level, len(text))`
- Any keypress clears sticky messages (or only Esc, if you want to be stricter)
- Every message also gets appended to a capped history buffer

If you share your framework (Ratatui, Bubble Tea, Textual, ncurses, …) or point me at the code once it's in this directory, I can write this into your status-line component.
