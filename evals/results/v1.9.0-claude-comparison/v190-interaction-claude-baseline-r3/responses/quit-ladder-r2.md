Use a fixed precedence: **Ctrl+C is checked first, the focused widget comes next, then Esc unwinds one layer per press, and q comes last.**

## 1. Ctrl+C: global, checked before anything else
Intercept it before keys reach the focused widget, so no component can swallow it.
- If an operation is running (fetch, long task), the first Ctrl+C cancels it.
- Otherwise it quits. If there's unsaved state, ask for confirmation, and let a second Ctrl+C force the quit.
- Always restore the terminal (alt screen, raw mode, cursor) on the way out, including on panic.

## 2. The focused widget gets the key next
A focused text input must receive `q` as a letter. This is the main problem with "q quits from anywhere": users can't type "query" in a search box. The input can also claim Esc, but only when it has something to undo (see below).

## 3. Esc: close one layer per press, innermost first
Five Esc meanings is fine if they form a strict stack and each press undoes exactly one layer:

| Priority | Esc does… |
|---|---|
| 1 | Dismiss a transient (autocomplete, tooltip, context menu) |
| 2 | Leave input/edit mode, keeping the text. Optionally a second press clears it. |
| 3 | Close a modal or dialog (same as Cancel, never Confirm) |
| 4 | Clear the selection or active filter in the current view |
| 5 | Go back one level in the navigation hierarchy |
| Root | **Nothing happens.** Esc should never quit. |

The rule is that Esc never skips a layer and never does anything destructive. Users will press it repeatedly to get out of something, so landing at the root and stopping there is the safe end point.

## 4. q: quits only in normal mode
- It's active only when no text input has focus.
- I'd make it **quit the app from any depth**, keeping your current behavior, and let Esc handle going back. That gives each key one job. The alternative, vim/less style where q closes the current view and quits only at the root, duplicates Esc and makes q's meaning depend on depth.
- Ask for confirmation if quitting would lose work.

## Practical details
- **Show what Esc will do** in the status bar or footer, e.g. `esc close search · q quit`. With five meanings, this hint makes the behavior predictable.
- **Set a short escape delay** (around 25ms; `ESCDELAY` in curses, or your framework's equivalent). Otherwise Esc feels laggy, because the terminal waits to see whether the Esc starts an Alt/arrow-key sequence.
- **Implement Esc as a single handler that walks the stack** rather than scattering checks through each view. That makes it hard to break the one-layer-per-press rule.

If you share your key handling code, I can check it against this order.
