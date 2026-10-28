Treat the text field as a small multiline editor, with predictable shell-style history and contextual completion.

| Area | Recommended behavior |
|---|---|
| Typing and paste | Insert at the cursor. Preserve pasted newlines and treat each paste as one undo step. Pasting must never submit. |
| Movement | Support arrows, Home/End, and platform-appropriate word movement. |
| Editing | Support Backspace/Delete, word deletion, undo/redo, and familiar line-editing shortcuts where the terminal permits them. |
| Submission | Enter submits; Shift+Enter inserts a newline. Provide a configurable alternative such as Ctrl+J because some terminals cannot distinguish Shift+Enter. |
| During a run | Keep the field editable so users can prepare their next message. Make any queue or interrupt behavior explicit. |
| History | Up/Down move within multiline text first. At the first/last line, they navigate previous/next prompts. |
| Draft preservation | Save the current draft and cursor before entering history; restore them when navigating forward past the newest entry. Editing a recalled prompt must not change the stored entry. |
| History search | Ctrl+R opens incremental search. Keep failed or canceled submissions out of history. |
| Completion | Complete slash commands, file references, mentions, and arguments based on cursor context. Show a menu with a clearly highlighted candidate. |
| Escape | Close completion/search first. Otherwise preserve the draft; don’t silently clear it. |

**Use Tab for completion while the composer has focus.**

- If a completion menu is open, Tab accepts the highlighted candidate; Enter can also accept it, without submitting the message.
- If there’s one valid completion, Tab inserts it.
- If there are several, Tab opens the menu; arrows navigate and Shift+Tab moves backward.
- If nothing is completable, leave the text unchanged. Don’t insert a tab character or unexpectedly move focus.
- Offer explicit focus navigation, such as F6/Shift+F6, and show it in help. If keyboard accessibility requires Tab-based focus traversal, provide a mode where Tab moves focus and another shortcut opens completion.

Keep completion **explicit by default**: displaying suggestions is fine, but accepting them should require a deliberate action. After acceptance, a subsequent Enter submits.

A compact footer can teach the essentials: `Enter send · Shift+Enter newline · Tab complete · ↑ history · F6 focus`. Only advertise shortcuts your terminal input layer can actually detect.