**Go inline with `<Static>` unless you need to change messages after they've been printed.** For a streaming chat client, inline wins on the things people actually use every day. Alternate screen is worth it only if you're really building an app with panes and interactive history.

## Why inline is the better default

You get these from the terminal for free:
- **Native scrollback.** The mouse wheel, Shift+PgUp, and tmux copy-mode all work.
- **Native text selection and copy.** This matters a lot for code blocks. Alt-screen apps that capture the mouse break it.
- **Terminal search** (Cmd+F) across the whole conversation.
- **The transcript stays after exit.** Users can scroll up and copy something after quitting.
- **Less to build.** No scroll view, no virtualization, no search, no selection handling.

## What inline costs you, and how to handle it

1. **Anything in `<Static>` is frozen.** You can't collapse tool output, edit a message, or update a status badge on an old turn. Decide what's final before you commit it.
2. **The live region has to stay shorter than the terminal.** Ink redraws the dynamic area by erasing lines upward. Once that area is taller than the viewport, it can't erase what scrolled off, and you get duplicated or garbled output. This is the most common bug with this approach. For long streaming responses:
   - Commit finished blocks (paragraphs, closed code fences, list items) to `<Static>` as the stream goes.
   - Keep only the unfinished tail, plus the spinner and input box, in the live region.
   - Cap the tail's height. If one block grows too long, like a huge code fence, show only its last N lines live and commit the full block when it closes.
3. **No reflow on resize.** Committed output keeps the width it was printed at. Most users accept this. Your options are to live with it, or clear and reprint on resize, which wipes their scrollback, so I wouldn't.
4. **Batch tokens before rendering.** Re-rendering on every token causes flicker and burns CPU. Buffer tokens and render at about 30fps, or once per line.
5. **Keep stray output out of the frame.** A raw `console.log` corrupts Ink's frame, so route logging through Ink or to a file.

## When alternate screen is the right call

- You want collapsible or expandable tool calls, or the ability to edit and re-run earlier turns.
- You want a multi-pane layout, such as a sidebar of conversations or a file preview.
- You need correct reflow on resize.
- You're fine building scrolling, search, a copy mode, and virtualization for long transcripts yourself, and printing a summary on exit because the screen disappears.

## A middle option

Keep the main chat inline and open the alternate screen only for modal views: a full transcript pager, a diff viewer, a session picker. Restore the inline view when the user closes it. That gives you rich views where they help without losing native scrollback for the conversation.

If you share your current component structure, I can sketch how to split committed blocks from the live tail, including how to handle code fences that aren't closed yet. That's the hardest part to get right.
