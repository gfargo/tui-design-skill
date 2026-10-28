Your input field should behave like a readline/fish prompt. Give it the standard editing keys, `↑`/`↓` history that only fires at the field's edges, and dimmed ghost-text suggestions. For Tab: **it completes when there's something to complete, and moves focus otherwise.** Because the field claims Tab, also give users a way to move focus that always works: `Esc` then `Tab`, or a dedicated key.

## Editing keys

| Key | Action |
|---|---|
| `←` `→` `Home` `End` | Move the cursor |
| `Backspace` / `Delete` | Delete a character |
| `Ctrl+W` | Delete the previous word |
| `Ctrl+U` / `Ctrl+K` | Delete to the start / end of the line |
| `Ctrl+A` / `Ctrl+E` | Aliases for Home / End only |

`Ctrl+A` can't be the only route to line-start. GNU screen uses it as its prefix key, and many tmux setups rebind it the same way, so those users never get the keypress. `Ctrl+B` (tmux) and many Ctrl/Alt keys under Zellij have the same problem. Make sure every action also has a key that doesn't need Ctrl or Alt.

## History

- `↑`/`↓` recall earlier entries only when the cursor is on the first or last line of the field. In a single-line field, every press recalls. In a multi-line draft, the arrows move between lines until the cursor reaches an edge, so users don't lose their draft while navigating it.
- Save history across sessions, and skip consecutive duplicates.

## Completion and ghost text

- Show the top suggestion dimmed after the cursor, like fish does. `→` or `End` at the end of the line accepts it.
- If several candidates match, the first Tab opens a list. Later presses cycle through it or narrow it.
- `Esc` closes the completion popup and does nothing else. That's step 2 of the Esc ladder (cancel → close → clear → back), so one press never closes the popup and also clears the draft or quits.

## Tab, step by step

1. **A completion is available** (slash command, `@file`, a path): Tab completes. With several matches, the first press shows the list.
2. **Nothing to complete**: Tab moves focus to the next pane, such as the transcript or a tool-output panel.
3. **Reliable focus exit**: since what Tab does depends on what you've typed, users need a way out that always works. `Esc` leaves the field, then `Tab`/`Shift+Tab` cycle panes. A dedicated jump key or numbered panes (`1`–`9`) also work.
4. **Don't bind `Ctrl+I` separately.** In the legacy key encoding it's the same byte as Tab.
5. **Never insert a literal tab character** in a chat field. If users need indentation, accept it through paste.

## Enter and newlines

- `Enter` sends.
- `Shift+Enter` is only distinguishable from `Enter` if the terminal supports the kitty keyboard protocol. Treat it as a bonus, and also provide:
  - `Alt+Enter`
  - `Ctrl+J`, which sends a line feed rather than Enter's carriage return, so it's distinct even in the legacy encoding
  - a trailing `\` followed by `Enter`
- Show the newline key where users will see it:

```
┌ 60 cols ─────────────────────────────────────────────────┐
│ > refactor the parser to use /reviewer-agent█ --strict   │  ← ghost text, dimmed
│                                                          │
│ Enter send · Alt+Enter newline · Tab complete · ↑ history│
└──────────────────────────────────────────────────────────┘
```

At 60 columns, shorten the hint to `Enter send · Alt+⏎ nl · Tab ⇥`, or drop the history hint first. Users find history on their own; they won't guess the newline key.

- **Bracketed paste**: pasted text, newlines included, goes into the field and never submits. This matters most in an agent TUI, where people paste stack traces.

## Other keys around the field

- `Ctrl+C` first cancels a running agent turn. If nothing is running and the draft is empty, it quits. If there's an unsent draft, the first press clears it or warns `Press Ctrl+C again to quit`.
- While the field has focus, `q`, `/`, `?`, and `hjkl` are just letters. Single-letter shortcuts only work after focus leaves the field.

## Tests

Most of this can be checked without a terminal by feeding synthetic key events into the field's state:
- Tab with zero, one, and many candidates
- `↑` on a middle line of a multi-line draft (should move the cursor, not recall)
- Paste containing `\n` (should insert, not submit)
- `Esc` with the popup open, then again with it closed
- Ghost text next to CJK or emoji, measured in terminal cells rather than string length

If you tell me your framework (Ink, Bubble Tea, Ratatui, Textual…), I can show how it handles these keys, including whether it can detect `Shift+Enter` and how it enables bracketed paste.
