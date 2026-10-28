The working directory is empty, so this is general guidance and isn't tied to your code. Tell me your framework (Ink, Bubble Tea, Ratatui, Textual, prompt_toolkit…) and I can make it specific.

## Editing: match readline and Emacs keys

People will type into this field with muscle memory from their shell. Anything that works differently from bash or zsh will feel broken.

**Must-have**
- **Moving the cursor:** ←/→, Ctrl-A/Ctrl-E (or Home/End) for start/end of line, and Alt-B/Alt-F (or Ctrl-←/→) to jump by word.
- **Deleting:** Backspace, Delete/Ctrl-D (when the field isn't empty), Ctrl-W to delete the previous word, Ctrl-U to delete to the start of the line, Ctrl-K to delete to the end, and Alt-Backspace or Alt-D to delete by word.
- **Yank:** Ctrl-Y pastes the last thing Ctrl-W/U/K deleted. Keep a small kill ring for this. It's separate from the system clipboard.
- **Undo:** Ctrl-_ or Ctrl-Z. Group keystrokes into word-sized steps so undo doesn't remove one character at a time.
- **Multiline:** Enter submits. Shift-Enter, Alt-Enter, or Ctrl-J inserts a newline, and so does a trailing `\` followed by Enter. Many terminals send the same bytes for Shift-Enter and Enter. Turn on the kitty keyboard protocol or xterm `modifyOtherKeys` if you can, and keep Alt-Enter and `\` as fallbacks.
- **Bracketed paste:** turn on `\e[?2004h`. Pasted newlines must not submit the prompt. Large pastes should become a placeholder chip such as `[Pasted 240 lines]` so they don't take over the screen, and the full text gets expanded when the prompt is sent.
- **Wide characters:** handle wide and combining characters (CJK, emoji) correctly. Measure with grapheme clusters and `wcwidth`, not byte or code-point counts. Wrap lines softly and keep the cursor in the right place across wrapped lines.

**Nice-to-have:** Ctrl-T to swap two characters, opening the prompt in `$EDITOR` (Ctrl-X Ctrl-E or Ctrl-G), and an optional vi mode.

## History

- **Keep it per project:** store history in an append-only file (JSONL works well), keyed by working directory, with a global fallback. Write each entry when it's submitted so a crash doesn't lose it, and limit the file to around 1–5k entries.
- **↑/↓:** these only move through history when the cursor is on the first or last line of the buffer. Otherwise they move the cursor up and down inside a multiline prompt. This is the most common bug in agent TUIs.
- **Save the draft:** keep whatever the user was typing before they started browsing, and bring it back when they press ↓ past the newest entry.
- **Prefix search:** if the user has typed `fix`, ↑ steps only through entries that start with `fix`, as in fish or zsh.
- **Ctrl-R:** incremental reverse search, ideally as a fuzzy-filtered popup.
- **Removing duplicates:** don't save an entry that's the same as the previous one. Don't save entries that start with a space, if you want to follow the bash convention.
- **Secrets:** consider leaving out anything that looks like a secret.

## Completion

You'll want completion for several kinds of token, each with its own trigger:

| Trigger | Completes |
|---|---|
| `/` at the start of the line | Slash commands, with descriptions |
| `@` | File paths (fuzzy, respecting `.gitignore`), and also symbols or URLs if you support them |
| `!` at the start | Shell mode, with path and command completion |
| No trigger | Optionally, a ghost-text suggestion from history (gray inline text, as in fish) |

Behavior:
- **Opening the menu:** typing a trigger character opens the menu automatically. It filters as the user keeps typing and closes on Space or Esc, or when nothing matches.
- **Ranking:** use fuzzy matching. Rank recently and often used items higher.
- **Display:** show at most about 8–10 rows, with the selected row highlighted and a one-line description. Draw the menu above the input when the input sits at the bottom of the screen.
- **Speed:** debounce the file index or build it once in the background. The menu must never block typing.
- **Accepting a choice:** insert the chosen item as a single unit. For example, an `@file` should be removed as a whole by one Backspace, or at least be clearly highlighted.

## Tab

In an agent TUI, Tab has three possible jobs: completion, moving focus, and toggling a mode. Give it one main job and make what it does depend on the current state:

1. **Completion menu open:** Tab accepts the selected item. Shift-Tab or ↑/↓ change the selection, and Enter also accepts. Don't let Enter submit the prompt while the menu is open.
2. **Ghost suggestion showing:** Tab (or →/Ctrl-E at the end of the line) accepts it.
3. **A completable token at the cursor** (`/xx`, `@src/fo`): Tab opens the menu, or fills in the longest common prefix if exactly one item matches. Keep this similar to shell behavior.
4. **Nothing to complete:** do nothing, or insert spaces only if you deliberately want literal tabs in prompts (most agents don't). Don't move focus away from the input without warning. People hit Tab by reflex, and losing the cursor is worse than nothing happening.

Other points:
- **Shift-Tab:** use it for a global mode switch, such as plan, auto-accept, or normal, but only when no menu is open. Show the current mode near the input so the switch is visible.
- **Moving focus:** if you need to move between panes, use something explicit like Ctrl-O, F-keys, or Esc then a key. Don't use Tab for this while the input has focus.
- **Detecting the keys:** Tab arrives as `\t` (same as Ctrl-I). Shift-Tab is usually `\e[Z`. Ctrl-Tab often can't be detected reliably, so don't depend on it.
- **Esc:** it closes the menu first, then clears the selection or ghost text, and only then does its global job (such as interrupting the agent). Give double-Esc its own action, for example clearing the input or opening a list of earlier messages to edit.

## Agent-specific extras

- **Typing while the agent runs:** keep the input editable during a run, and either queue what's submitted or send it in as a mid-run message. Make it clear which one happens.
- **Ctrl-C:** first press clears the input or interrupts the run. A second press within about 1 second exits.
- **Drafts:** keep the draft if the user interrupts, and possibly across restarts.
- **Hint line:** show a short line under the input with context-dependent hints, such as `Tab accept · Esc close`.

If you share your stack, I can sketch the key-handling state machine for it.
