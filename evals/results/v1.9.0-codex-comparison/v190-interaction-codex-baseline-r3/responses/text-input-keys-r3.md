Treat the field as a small multiline editor, with predictable editing and explicit completion.

| Area | Recommended behavior |
|---|---|
| Submit | **Enter** sends; **Shift+Enter** inserts a newline where supported. Offer **Ctrl+J** as a terminal-friendly newline alternative. |
| Editing | Support arrows, Home/End, Backspace/Delete, word movement and deletion, plus familiar Ctrl+A/E, Ctrl+U/K, and Ctrl+W shortcuts where the terminal exposes them. |
| Paste | Use bracketed paste. Preserve newlines and never submit pasted text automatically. |
| Undo | Support undo/redo; group a paste or completion acceptance into one undo step. |
| History | Up/Down moves within multiline text. At the first/last line, it navigates submitted prompts. Preserve the unfinished draft and restore it when navigating forward past the newest entry. |
| History search | Ctrl+R searches previous prompts. Editing a recalled prompt creates a draft; it doesn’t modify history. |
| Completion | Suggest commands, paths, mentions, or other concrete tokens based on the cursor position. Show what will be replaced. Avoid silently rewriting unrelated text. |
| Escape | Dismiss completion or search first. Never erase the draft as a side effect. |

**Give Tab a clear priority order:**

1. **Completion menu open:** Tab accepts the highlighted candidate; arrows change the selection; Escape dismisses it. Enter may also accept, but must consume that keypress so it cannot send the prompt.
2. **A completable token at the cursor:** Tab requests completion. One match inserts it; multiple matches open the menu.
3. **Otherwise:** Tab moves focus to the next control; Shift+Tab moves backward.

Avoid using Tab for both completion acceptance and indentation. If you offer a dedicated code-editing mode, Tab can indent there, with an explicit way to leave the editor.

Keep this discoverable with a short contextual hint such as `Enter send · Ctrl+J newline · Tab complete`. Test the actual terminal key sequences: Shift+Enter, Ctrl+Enter, and some modified editing keys are not distinguishable in every terminal.