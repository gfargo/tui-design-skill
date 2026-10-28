The text field is the core of an agent TUI, so make it behave like the shell users already know. Keep `Tab` for completion only when there is something to complete; otherwise let it move focus.

## Editing keys

| Keys | Action |
|---|---|
| `←` `→` `Home` `End` | Move the cursor |
| `Backspace` / `Delete` | Delete a character |
| `Ctrl+W` | Delete the previous word |
| `Ctrl+U` / `Ctrl+K` | Delete to the start / end of the line |
| `Ctrl+A` / `Ctrl+E` | Start / end of line. Use these only as extra shortcuts for `Home`/`End`, because GNU screen uses `Ctrl+A` as its prefix key |

Don't bind `Ctrl+I`, `Ctrl+H`, `Ctrl+M` or `Ctrl+[` to anything. In most terminals they send the same bytes as `Tab`, `Backspace`, `Enter` and `Esc`.

## Submit vs. newline

- **`Enter` sends.** A modifier key inserts a newline.
- **Don't make `Shift+Enter` the only newline key.** Terminals can only tell it apart from `Enter` when the kitty keyboard protocol is on. Provide `Alt+Enter` and `Ctrl+J` too, plus a trailing `\` then `Enter` as a third option.
- **Show the newline key** in the placeholder or footer, e.g. `Enter send · Alt+Enter newline`.
- **Turn on bracketed paste.** Pasted newlines should be inserted into the field and never submit it. This matters a lot when people paste stack traces into an agent.

## History

- `↑`/`↓` recall previous prompts **only when the cursor is on the first or last line** of the field. On other lines they move the cursor, so editing a multi-line draft still works.
- Save history across sessions and skip consecutive duplicates.
- One addition of my own, not from the skill reference: if the user has typed an unsent draft and scrolls into history, keep the draft as the newest entry so `↓` brings it back. Losing a long prompt to an accidental `↑` is a bad experience.

## Completion and ghost text

Use fish-style suggestions. Show the suggestion dimmed after the cursor, and accept it with `→` or `End`:

```
 > /mod█el claude-opus-5-5                       ← dim ghost text
 ───────────────────────────────────────────────────────────
 Enter send · Alt+Enter newline · → accept · Tab complete
```

At 60 columns, cut the footer down to `Enter send · Alt+Enter ⏎ · → accept`. Never let it wrap onto a second line.

In an agent TUI, good things to complete are slash commands, `@file` paths, and model or tool names.

## How to handle Tab

1. **One match:** `Tab` completes it in place.
2. **Several matches:** the first `Tab` shows the candidates in a popup. `Tab` or arrows step through them, and `Enter` or `Tab` accepts.
3. **No match:** `Tab` moves focus, as it does elsewhere in the app.

Since the field takes `Tab` whenever a completion exists, users need a reliable way to leave it:

- **`Esc`, then `Tab`.** `Esc` closes the completion popup first. With no popup open, it releases focus from the field.
- **A dedicated focus key**, such as numbered panel jumps (`1`–`9`) or a key shown in the footer, for people who don't want the two-step.

`Esc` should do one step per press: cancel a running agent turn, then close the popup, then clear the field, then go back. It never quits. `Ctrl+C` stops the running agent turn first. When nothing is running it quits, but if there's an unsent draft, the first press shows `Press Ctrl+C again to quit` so the draft isn't lost.

## Tests

- **Unit-test the key handling** with fake key events, no terminal needed. Cover: `Tab` with zero, one and many matches, `↑` in the middle of a multi-line draft (moves the cursor, doesn't recall history), and a pasted multi-line string (doesn't submit).
- **Run one real-terminal check inside tmux.** Confirm `Alt+Enter` and `Ctrl+J` insert newlines, and that `Esc` responds quickly.

If you tell me your framework (Ink, Textual, Bubble Tea, Ratatui), I can show how it handles bracketed paste, the kitty keyboard protocol and `Tab` focus.
