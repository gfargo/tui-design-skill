Use a **modeless, multiline composer with familiar shell editing**. The main loop should stay simple: write, recall or complete, send.

| Behavior | Recommended contract |
|---|---|
| Basic editing | Arrows, Home/End, Backspace/Delete. Move and delete whole Unicode characters correctly. |
| Editing shortcuts | `Ctrl+W` deletes the previous word; `Ctrl+U` deletes to line start; `Ctrl+K` deletes to line end. `Ctrl+A/E` alias Home/End, since multiplexers may intercept them. |
| History | `↑` recalls older entries only on the first line; `↓` recalls newer entries only on the last. Otherwise they move within the draft. Persist history across sessions and skip consecutive duplicates. Preserve the current draft so returning past the newest entry restores it. |
| Ghost suggestions | Show suggested text dimmed after the cursor. At the end of the typed text, `→` or End accepts it; elsewhere those keys retain normal cursor movement. |
| Sending | Enter sends. `Alt+Enter` or `Ctrl+J` inserts a newline. Offer Shift+Enter when the terminal reports it distinctly, plus trailing `\` then Enter as a fallback. |
| Pasting | Enable bracketed paste: pasted newlines insert text and **never send**. |
| Printable shortcuts | While editing, `q`, `/`, `?`, and navigation letters are ordinary text. |

**Give Tab an explicit priority order:**

1. **One completion matches:** insert it.
2. **Several match:** first Tab opens the candidate list. Arrow keys select; Tab accepts the selected candidate. Acceptance edits the draft without sending.
3. **No completion exists:** Tab moves focus forward; Shift+Tab moves backward.
4. **To leave without completing:** provide `Esc`, then Tab. Esc dismisses the completion popup first and preserves the draft. If a request is running, Esc cancels that first, so advertise the applicable action.

Show the current meaning in the footer: `Tab complete`, `Tab accept`, or `Tab next pane`. Never complete and move focus on the same keypress. Don’t assign another action to `Ctrl+I`: legacy terminals encode it identically to Tab.

Assuming a full-screen agent session, keep the transcript above the composer:

```text
Wide                                     60 columns
Agent / project              Tools       Agent / project
…conversation…               …           …conversation…
                                         
> Explain this change_                   > Explain this change_
Enter send · Alt+Enter newline            Enter send · Alt+Enter newline
Tab complete · Esc cancel                Tab complete · Esc cancel
```

At 80×24, cap composer growth and scroll its contents. At 60 columns, hide the tools sidebar and keep completion candidates within the composer’s width; truncate descriptions before candidate names. A reasonable declared minimum is 60×10, below which show “terminal too small” while retaining the draft.

For this layout, the clutter budget is **zero nested borders, one focus cue, and two hint rows**—about 8% of a 24-row screen. Remove repeated “Input” labels, decorative boxes, and duplicate focus markers.

Verify the ambiguous cases: history restores an unfinished draft, completion acceptance never sends, multiline paste never sends, and newline/focus bindings work inside tmux and a legacy terminal.