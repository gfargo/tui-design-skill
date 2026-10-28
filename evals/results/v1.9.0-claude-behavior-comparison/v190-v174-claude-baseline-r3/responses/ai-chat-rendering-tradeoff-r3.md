I'd go **inline with `<Static>`** for a chat client, unless you need to change messages after they've been printed.

## Why inline usually wins for chat

- **Users get native terminal behavior for free.** Scrollback, Cmd+F search, mouse selection and copy, and tmux copy-mode all just work. With the alternate screen you have to rebuild every one of these, and copy/paste is the one people miss most.
- **The transcript stays after exit.** People scroll up to grab a command or code block the model gave them. On the alternate screen, all of that disappears when the app closes.
- **It matches what the app is.** A chat transcript only grows at the bottom, which is exactly how a terminal works.

## The main risk with inline: tall live regions

Ink redraws the dynamic (non-`<Static>`) area by erasing the previous frame and printing a new one. Once that area is taller than the viewport, Ink can't reach the lines that have scrolled off. The result is flicker, duplicated output or broken scrollback. A long streaming response triggers this easily.

How to avoid it:

1. **Move finished parts of the stream into `<Static>` as they complete.** Don't wait for the whole message. Split at block boundaries: a blank line between paragraphs, a closed code fence, the end of a list. Only the unfinished block stays in the live region.
2. **Keep the live region short:** the partial block, a spinner or status line, and the input box. If one block gets very long (say a 200-line code block), show only its last N lines live and commit the full block when it closes.
3. **Batch token updates.** Collect tokens and re-render every ~16–50 ms rather than once per token. This cuts flicker a lot.
4. **Accept that printed output is fixed.** You can't collapse, restyle or edit anything already in `<Static>`, and a resize won't re-wrap it properly. Plan your UI around that.

## When the alternate screen is the better choice

Choose it if you need any of these:
- Collapsible or expandable sections, like tool output or "show thinking"
- Editing, regenerating or branching earlier messages in place
- Moving between messages with the keyboard, or side panels and multi-pane layouts
- Text that re-wraps correctly when the window is resized

The costs: Ink has no built-in scroll view, so you'll write your own viewport (only rendering the visible lines, tracking scroll offset, sticking to the bottom while streaming). If you capture the mouse for scrolling, native text selection stops working unless the user holds a modifier key. You'll also need your own search and copy. A common way to soften the exit problem is to print the transcript, or its file path, to the main screen when the app quits.

## Middle ground

Some tools stay inline by default and open the alternate screen temporarily for specific views, like a transcript browser, a diff viewer or a picker. You keep native scrollback for the main flow and get full control where you need it.

**Bottom line:** if your list of needs is "stream responses, render markdown, take input," go inline, commit finished blocks to `<Static>` as they stream in, and keep the live region small. Switch to the alternate screen only if being able to change past messages is central to your design.
