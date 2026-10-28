Use a **modeless, multiline composer with familiar shell editing**. While it has focus, printable keys—including `q`, `/`, and `?`—insert text.

| Area | Recommended behavior |
|---|---|
| Movement | Arrows, Home/End; Ctrl+A/Ctrl+E as line-start/end aliases. Keep Home/End because multiplexers can capture Ctrl+A. |
| Deletion | Backspace/Delete; Ctrl+W deletes the previous word, Ctrl+U deletes to line start, Ctrl+K deletes to line end. |
| History | Up recalls older entries only on the first line; Down recalls newer entries only on the last line. Otherwise they move the cursor vertically. Persist history across sessions and skip consecutive duplicates. |
| Draft preservation | Save the current draft before entering history; restore it when moving past the newest entry. Editing a recalled entry must not change stored history. |
| Ghost suggestions | Show suggested text dimmed after the cursor. Right or End accepts it when at the end of entered text; elsewhere those keys retain normal movement. |
| Sending | Enter sends. Alt+Enter or Ctrl+J inserts a newline; also support trailing `\` then Enter. Offer Shift+Enter when the terminal reports support, and display the available newline binding. |
| Paste | Enable bracketed paste. Pasted newlines become field content and **never submit**. |

**Give Tab an explicit, context-dependent contract:**

1. **One completion exists:** Tab inserts it.
2. **Several completions exist:** the first Tab opens the candidate list. Arrows choose; Tab accepts the highlighted candidate. Enter may also accept while the list is open, but that press must never send the message.
3. **No completion exists:** Tab moves focus to the next control.
4. **A completion list is open:** Esc closes it without changing the draft.

Because completion takes priority, provide a reliable escape: **Esc leaves text-entry focus without clearing the draft; Tab then cycles panels**. If a completion list is open, the first Esc closes it and the next leaves the field. Outside completion, Shift+Tab moves backward through focus. Do not use Ctrl+I as a separate action: legacy terminals encode it identically to Tab.

Keep hints contextual:

```text
Wide
> Review @src/agent.ts and explain the retry behavior_
Enter send · Alt+Enter newline · Tab complete · Esc leave

60-column split
> Review @src/agent.ts and explain
  the retry behavior_
Enter send · Alt+Enter newline · Tab complete
```

When candidates appear, replace the hint with `↑↓ choose · Tab accept · Esc close`.

At 80×24 and 60 columns, keep the composer full width, wrap input, place candidates above it, and hide ancillary panes first. Cap composer growth so the transcript remains visible, then scroll within the field. Below the measured minimum needed for input and hints, show a truthful “terminal too small” state.

Keep chrome sparse: no nested composer borders, repeated “Input” labels, or marker on every candidate. One selection cue and one contextual hint row are enough.