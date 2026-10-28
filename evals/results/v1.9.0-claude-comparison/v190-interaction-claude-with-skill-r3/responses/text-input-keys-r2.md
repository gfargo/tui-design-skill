**Short version:** your prompt field should own `Tab`. When a completion exists, `Tab` completes it. To leave the field, the user presses `Esc` and then `Tab`, or a dedicated focus key. Only fields that never complete anything should let `Tab` move focus. In an agent TUI the text field is the main thing people use, so it should behave like a good shell line editor.

## Editing keys

| Keys | Action |
|---|---|
| `←` `→`, `Home` `End`, `Backspace` `Delete` | The basic keys, which always work |
| `Ctrl+W` | Delete the previous word |
| `Ctrl+U` / `Ctrl+K` | Delete to the start / end of the line |
| `Ctrl+A` / `Ctrl+E` | Aliases for `Home` / `End`. They must never be the only way: GNU screen uses `Ctrl+A` as its prefix key |

`Ctrl+C` should keep its usual meaning. It cancels the running agent turn first, and with nothing running it quits. If quitting would lose something, such as a half-typed prompt, the status line says "Press Ctrl+C again to quit" and a second press quits. Don't give it a separate meaning inside the field.

## Submitting and newlines

- **`Enter` sends. A modifier inserts a newline.** Without the kitty keyboard protocol, `Shift+Enter` looks the same as `Enter`, so add fallbacks:
  - `Alt+Enter`
  - `Ctrl+J` (it sends a line feed, which the terminal keeps separate from `Enter`)
  - a trailing `\` followed by `Enter`
- **Show the newline key** in the placeholder or footer, e.g. `Enter send · Alt+Enter newline`.
- **Turn on bracketed paste.** Pasted newlines are then inserted as text and never submit the prompt. This matters a lot for agent prompts, because people paste multi-line code and logs into them.

## History

- `↑` / `↓` recall earlier prompts only when the cursor is on the **first or last line** of the field. On other lines they move the cursor, so editing a multi-line prompt still works.
- **Save history across sessions** and skip consecutive duplicates.
- Nice extras: keep the unsent draft so `↓` past the newest entry brings it back, and offer a fuzzy history search in the style of atuin.

## Completion (slash commands, `@file` mentions)

- **Ghost text:** show the single best suggestion dimmed after the cursor, as fish does. `→` or `End` accepts it.
- **`Tab`:**
  - If exactly one candidate matches, `Tab` completes it.
  - If several match, the first press opens a list of candidates and later presses cycle through them.
  - If nothing matches, `Tab` does nothing. It does not jump focus while the user is typing.
- **`Esc`** closes the completion popup and does nothing else. Each `Esc` press handles one level, innermost first: cancel the running request, then close the popup, then clear, then go back. It never quits.

## Handling Tab

1. **The prompt field owns `Tab`.** Moving focus with `Tab` in a field that also completes makes the key unpredictable: the same press does two different things depending on what you typed.
2. **Leaving the field:** `Esc` releases focus to the panels, and then `Tab`/`Shift+Tab` cycle through them. You can also add a dedicated key, such as numeric panel jumps like lazygit's `1`–`9`. Show that key in the footer.
3. **Don't bind `Ctrl+I` separately.** In the legacy key encoding it sends the same byte as `Tab`. The same goes for `Ctrl+Tab`, which the legacy encoding can't send at all, so treat it as an optional shortcut, never the only way.
4. **While the field has focus, printable keys are letters.** Single-letter app shortcuts like `q`, `/` and `?` only work after `Esc` moves focus out of the field.

## Layout at 60 columns

```
┌──────────────────────────────────────────────────────────┐
│ > refactor the auth module using @src/au│th/session.ts    │  ← dimmed ghost text after cursor
│   @src/auth/session.ts                                   │  ← candidate list (several matches)
│   @src/auth/middleware.ts                                │
└──────────────────────────────────────────────────────────┘
 Enter send · Alt+Enter newline · Tab complete · Esc close
```

At 60 columns, cut the footer down to `Enter send · Alt+Enter ⏎ · Tab complete` instead of letting it wrap. If the input grows past about 5 lines, scroll inside the field and keep the transcript visible. Measure ghost text and the cursor position in terminal cells, not string length, or CJK text and emoji will put the cursor in the wrong place.

## What to test

Feed synthetic keys to the field's update logic and check the resulting state:
- `Tab` with zero, one and many candidates
- `↑` on the middle line of a multi-line prompt, which should move the cursor, not recall history
- a pasted block containing `\n`, which should not submit
- `Esc` with the popup open, which should close the popup only

Then add one PTY smoke test inside tmux to confirm `Alt+Enter` and a lone `Esc` actually reach the app.

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual or Ink), I can show how each of these maps onto its input widget.
