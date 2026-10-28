Your working directory is empty, so this answer isn't tied to any particular framework. It's a spec you can build against.

## Editing

Users will expect shell (readline/Emacs-style) keybindings without thinking about it:

| Keys | Action |
|---|---|
| `Ctrl-A` / `Ctrl-E`, `Home` / `End` | Start / end of line |
| `Ctrl-B` / `Ctrl-F`, arrows | Move one character |
| `Alt-B` / `Alt-F`, `Ctrl-←/→`, `Option-←/→` | Move one word. On macOS, Option-arrows arrive as `\eb`/`\ef` or `CSI 1;3D/C`, so handle all of them |
| `Ctrl-W`, `Alt-Backspace` | Delete the previous word |
| `Alt-D` | Delete the next word |
| `Ctrl-U` / `Ctrl-K` | Delete to start / end of line |
| `Ctrl-Y` | Paste back the last deleted text (keep a small history of deletions, not the system clipboard) |
| `Ctrl-_` | Undo. Group consecutive typing into one undo step |
| `Ctrl-G` or `Ctrl-X Ctrl-E` | Open the draft in `$EDITOR` and read it back on exit |

Things that get missed:
- **Multiline:** Enter sends the message. A newline should come from `Shift-Enter`, `Alt-Enter`, `Ctrl-J`, *and* a trailing `\` followed by Enter. Most terminals only report Shift-Enter if you turn on the kitty keyboard protocol or xterm's `modifyOtherKeys`, so the other options are your fallbacks.
- **Bracketed paste:** Turn it on (`\e[?2004h`). Newlines inside a paste are inserted as text and never send the message. Show large pastes as a placeholder like `[Pasted text, 140 lines]`, but send the full content.
- **Unicode:** Move the cursor and delete by whole visible characters (grapheme clusters), not bytes or code points. Measure width with wcwidth, since CJK characters and emoji take two columns. Wrap lines by display width.
- **Keys to leave alone:** Don't use `Ctrl-Z` for undo, because it suspends the process (SIGTSTP). Don't use `Ctrl-S`/`Ctrl-Q`, because terminals can use them for flow control.
- **Ctrl-C:** If there's text, clear it. If the field is empty, interrupt the agent. Pressing it twice in a row quits.

## History

- **Up/Down:** In a multiline draft, Up/Down move between lines. They only switch to history when the cursor is already on the first or last line.
- **Keep the draft:** Before showing older entries, save what the user was typing as a temporary entry 0. Pressing Down past the newest entry brings it back.
- **Editing old entries:** Edit a copy, so recalled entries never change in the history itself.
- **Prefix filter (optional):** If the user typed something before pressing Up, show only entries that start with it.
- **`Ctrl-R`:** Reverse incremental search with a match shown inline. Enter accepts it and Esc cancels.
- **Persistence:** Save one history file per project or working directory. Don't store a command twice in a row, cap the size (for example 1–5k entries), and append atomically or with a lock so several sessions don't corrupt the file.
- **Don't save:** Leave out entries that look like secrets, and consider leaving out bare slash commands.

## Completion

- **Triggers:** `/` at the start of the input completes commands. `@` anywhere completes file paths, fuzzy-matched and respecting `.gitignore`. Optionally, Tab after a path-like word completes it too.
- **Menu:** Show suggestions in a popup just below or above the input. Typing still goes to the input. While the popup is open, Up/Down (and `Ctrl-N`/`Ctrl-P`) move through suggestions instead of history.
- **Speed:** Build the file list in the background and limit how often you re-filter while the user types. Never block keystrokes on the file system.
- **Esc order:** Esc closes the popup first. Only when nothing is open does it interrupt the agent.

## Tab

Handle Tab as an ordered set of checks and stop at the first one that applies:

1. **Popup open:** Accept the highlighted suggestion and add a space or `/` after it as needed.
2. **Cursor right after a completion trigger** (`/cmd`, `@path`, a path):
   - One match: complete it inline.
   - Several matches: fill in their shared prefix and open the menu.
   - No matches: do nothing (optionally beep or flash).
3. **Otherwise:** Do nothing.

Don't insert a literal tab character. Terminals display tabs inconsistently and they break your width math. Any tabs that arrive in a paste should be kept in the text but drawn as spaces.

Also:
- **`Shift-Tab`** (`CSI Z`) is a good place for a mode toggle, such as plan / auto-accept / normal. That's an established convention in agent TUIs, and it doesn't interfere with completion.
- **Focus:** Don't let Tab move focus out of the input. Keyboard users lose their place, and in most terminals Tab can't be told apart from `Ctrl-I`.
- **While the agent is running:** Tab should still complete in the input, so users can type their next message ahead of time.

If you tell me your stack (Ink, Bubble Tea, Textual, ratatui, or something else), I can map this onto its key events and point out which pieces it already handles.
