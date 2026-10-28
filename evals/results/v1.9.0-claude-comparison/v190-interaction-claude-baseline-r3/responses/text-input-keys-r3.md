Your working directory is empty, so this is general guidance rather than advice tied to a framework. If you tell me what you're using (Ink, Bubble Tea, Ratatui, Textual, prompt_toolkit…), I can make it specific.

## Editing

Users bring shell muscle memory, so support the readline/Emacs keys at minimum:

| Keys | Action |
|---|---|
| `Ctrl-A` / `Ctrl-E`, `Home` / `End` | Start / end of line |
| `Ctrl-B` / `Ctrl-F`, `Alt-B` / `Alt-F` (and `Ctrl/Alt-←→`) | Move by character / word |
| `Ctrl-W`, `Alt-Backspace` | Delete previous word |
| `Ctrl-U` / `Ctrl-K` | Delete to start / end of line |
| `Ctrl-Y` | Paste back what the delete keys just removed (keep a small "kill ring" buffer) |
| `Ctrl-_` | Undo. Don't use `Ctrl-Z`, which suspends the process (SIGTSTP). |

**Multi-line input:**
- `Enter` submits.
- For a newline, accept `Shift+Enter` **and** at least one fallback: `Alt+Enter`, `Ctrl-J`, or `\` + `Enter`. Many terminals can't tell `Shift+Enter` apart from `Enter` unless you turn on the kitty keyboard protocol or `modifyOtherKeys`. Detect support and fall back if it's missing.
- Wrap long lines visually, and make sure the cursor moves through wrapped lines correctly.

**Paste:**
- Turn on bracketed paste. Newlines inside a paste must insert text, not submit.
- Collapse large pastes into a placeholder like `[Pasted 240 lines]` and expand it when the message is sent.

**Unicode:** Place the cursor by display width and grapheme cluster, not by byte or code point. Otherwise CJK text, emoji, and combining characters leave the cursor out of sync with the text.

**Control keys:**
- `Ctrl-C`: clears the input if there's text. If the input is empty, it interrupts the running agent, and pressing it twice exits.
- `Ctrl-D`: exits only when the input is empty.
- `Esc`: closes any open menu first. If none is open, it interrupts the agent.

**Optional:** a vi mode, behind a setting.

## History

- **Up/Down are context-sensitive.** In multi-line input, they move the cursor between lines. They only step through history when the cursor is already on the first line (Up) or the last line (Down).
- **Keep the draft.** Save the unsent text when the user starts browsing history, and restore it when they arrow back down past the newest entry.
- **Prefix filtering.** If the user typed something before pressing Up, only show history entries that start with it.
- **`Ctrl-R`** opens reverse incremental search, with the match highlighted inline.
- **Persistence:**
  - Save history to a file, ideally per project or working directory.
  - Store multi-line entries whole.
  - Drop an entry if it repeats the one just before it.
  - Cap the file size.
- **Privacy:** Skip saving entries that start with a space (shell convention), and consider skipping anything that looks like a secret.

## Completion

- **Triggers:**
  - `/` at the start of the input completes slash commands.
  - `@` completes file and path mentions, with fuzzy matching and gitignore respected.
  - Optionally, complete path-like tokens anywhere.
- **Menu:** Show a popup above or below the input that filters as the user types. Highlight the matched characters, and show a short description for each command.
- **Priority:** While the menu is open, it owns the keys:
  - `Up/Down` and `Ctrl-N/P` move through the list instead of history.
  - `Enter` and `Tab` accept the selection.
  - `Esc` closes the menu.
- **Async:** Debounce lookups, never block a keystroke, and throw away results that arrive after the input has changed.
- **Ghost text (optional):** Show a dim inline suggestion that `→` or `End` accepts when the cursor is at the end of the line. Don't let `Tab` accept both ghost text and menu items, or it becomes unclear what `Tab` will do.

## Handling Tab

The terminal sends Tab as byte `0x09`, which is the same as `Ctrl-I`, so you can't tell the two apart. Shift+Tab arrives as `ESC [ Z`. I'd resolve Tab in this order:

1. **Menu open:** accept the highlighted item. Or, if you prefer cycling, move to the next item, and let Shift+Tab move to the previous one.
2. **Cursor is on a completion trigger** (`/cmd`, `@path`, a path): finish the longest prefix all matches share. If that's ambiguous, open the menu. If there's exactly one match, insert it plus a trailing space.
3. **Nothing to complete:** do nothing, or show a quiet hint. **Don't insert a literal tab character.** Its display width depends on the terminal, it breaks your cursor-position math, and it's almost never what the user wanted in a prompt. If people need indentation, insert spaces.
4. **Pasted text containing tabs:** keep the tabs in the data that gets sent, but display them as spaces.

Don't use Tab to switch focus between panes. Users expect it to complete, and overloading it makes the behavior unpredictable. Use `Shift+Tab` (for things like cycling modes such as plan, auto-accept, normal) or a dedicated key for focus and mode changes.

**Dispatch order for each key press:** active modal or search (`Ctrl-R`) → completion menu → key bindings for the input field → insert as text. With that single chain, Tab, Up/Down, Enter, and Esc each do one predictable thing in each state.
