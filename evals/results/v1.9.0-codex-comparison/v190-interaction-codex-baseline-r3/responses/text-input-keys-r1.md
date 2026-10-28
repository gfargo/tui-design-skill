Treat the field as a **multiline prompt editor with familiar shell shortcuts**. Keep editing predictable, and make completion explicit.

| Area | Recommended behavior |
|---|---|
| Typing and paste | Insert at the cursor. Preserve multiline paste as one undo operation; pasting must never submit. |
| Movement | Left/Right by character, platform-supported shortcuts by word, Home/End by visual line. Support Ctrl+A/E for line start/end. |
| Deletion | Backspace/Delete by character; Ctrl+W deletes the previous word, Ctrl+U/K deletes to line start/end. |
| Undo | Support undo/redo, grouping ordinary typing sensibly. Completion acceptance should be undoable. |
| Submission | Enter submits; show a documented newline binding such as Alt+Enter. Support Shift+Enter where the terminal can distinguish it. Empty input does nothing. |
| History | Up/Down move through lines first; at the first/last logical line, navigate prompt history. Save the current draft and restore it when moving past the newest entry. |
| History editing | Recalled prompts become editable drafts; editing them never changes stored history. |
| History search | Ctrl+R opens searchable prompt history. Escape restores the previous draft. |
| Completion | Offer commands, paths, mentions, or agent names when the cursor context supports them. Show a selectable menu with descriptions and the exact replacement scope. |
| Escape | Close completion/search first, without losing text. Avoid making Escape silently clear the prompt. |

**Use Tab for completion while the prompt has focus.** Give it a consistent priority:

1. If a completion menu is open, Tab accepts the selected candidate.
2. Otherwise, if completion applies at the cursor, Tab opens the menu; a single unambiguous match can be inserted directly.
3. If completion does not apply, leave the text unchanged and give subtle feedback. Don’t unexpectedly submit, switch agents, or move focus.

Use Up/Down to select candidates, Enter to accept while the menu is open, and Escape to dismiss it. Accepting a completion must **not also submit** the prompt.

Reserve a separate, visible shortcut—such as F6—to cycle between the editor and other panes. Once focus is outside the editor, Tab/Shift+Tab can navigate controls normally. If your TUI uses conventional Tab focus navigation instead, preserve that convention and put completion on another binding; don’t make Tab ambiguously do both.

For code-heavy prompts, offer an explicit indentation mode where Tab indents and Shift+Tab unindents. Avoid guessing whether the user wants indentation from the text alone.

Terminal key support varies, especially for Shift+Enter and Ctrl+Space. Provide configurable bindings and display the active newline, completion, and focus shortcuts near the field.