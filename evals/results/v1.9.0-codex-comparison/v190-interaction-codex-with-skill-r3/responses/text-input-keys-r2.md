Use a **modeless, multiline chat composer with familiar editing keys**. Tab should complete when there’s a completion available and move focus otherwise—with an explicit way to leave the field even while suggestions exist.

Following the tui-design skill, I recommend this contract:

| Area | Behavior |
|---|---|
| Basic editing | Arrows, Home/End, Backspace/Delete. Move and delete whole grapheme clusters so emoji and combining characters survive editing. |
| Editing shortcuts | Ctrl+W deletes the previous word; Ctrl+U deletes to line start; Ctrl+K deletes to line end. Ctrl+A/E alias Home/End, but aren’t the only routes. |
| Printable keys | `q`, `?`, `/`, and navigation letters type text while the composer owns input. |
| History | Up recalls history only on the first line; Down only on the last line. Elsewhere they move within the draft. Persist history and skip consecutive duplicates. Preserve the current draft and restore it when returning past the newest entry. |
| Ghost text | Show suggested text dimmed after the cursor. Right or End accepts it when the cursor is at the suggestion boundary; elsewhere those keys retain normal editing behavior. |
| Sending | Enter sends. Alt+Enter or Ctrl+J inserts a newline. Offer Shift+Enter where the terminal reports it distinctly, plus trailing `\` then Enter as another fallback. |
| Paste | Bracketed paste inserts the whole text, including newlines, and **never submits**. |
| Cancellation | Esc dismisses completion without deleting the draft. Ctrl+C cancels running work first; an idle quit that would lose a draft warns before exiting. |

**Make Tab’s priority explicit:**

1. **One completion:** Tab inserts it without sending.
2. **Several completions:** the first Tab opens the candidate list. Arrows select; Tab accepts; Esc dismisses. If Enter also accepts candidates, it must consume that event rather than also send the message.
3. **No completion:** Tab moves focus forward; Shift+Tab moves backward.
4. **Leaving a completing field:** support **Esc, then Tab**. Dismiss suggestions and suppress automatic reopening until the next edit, so the next Tab reliably moves focus.

Don’t use Ctrl+I as a separate escape hatch: legacy terminals encode it identically to Tab. Likewise, Shift+Enter and Ctrl+Tab cannot be required routes.

Keep the footer contextual:

```text
Wide:
> Explain this failure|
Enter send  Alt+Enter newline  Tab complete  Esc then Tab focus

60 columns:
> Explain this failure|
Enter send  Alt+Enter newline  Tab complete
```

When candidates open, replace the hints with `↑↓ choose  Tab accept  Esc close`. Provide expanded help through a visible control; bare `?` still types into the composer.

For the surrounding layout, assume a persistent transcript above the composer. At 80×24, cap the composer’s growth and scroll within it. In a 60-column split, hide side panels and keep transcript, composer, and contextual hints. Below your declared minimum, show a truthful “terminal too small” state while retaining the draft.

The proposed composer needs **zero nested borders, one prompt marker, and one hint row**. Remove repeated “Input” labels and decorative status icons; keep the real terminal cursor visible in the field.

Before shipping, verify draft restoration after history browsing, completion acceptance never sending, multiline paste never sending, Unicode deletion, and Tab escape behavior in both a legacy terminal and tmux.