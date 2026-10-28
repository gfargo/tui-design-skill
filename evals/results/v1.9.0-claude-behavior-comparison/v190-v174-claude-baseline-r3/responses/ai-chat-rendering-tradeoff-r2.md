For a chat client I'd go **inline with `<Static>`**, unless you already know you need layout features that only the alternate screen gives you (listed at the end).

## Why inline fits a chat transcript

A transcript only ever grows at the bottom, and that's the case inline mode handles well:

- **The terminal does the hard parts for you.** Scrollback, mouse selection, copy, search (Cmd-F, tmux copy-mode) and scroll-wheel all work with no code from you.
- **The transcript outlives the process.** After the app exits, the conversation stays in the terminal, so users can scroll back or copy from it.
- **It plays well with tmux, ssh and logging tools.** Output is just text in the stream.

Building those yourself in alt-screen is a lot of work, and users will notice anything you get slightly wrong. Text selection is the worst case: once you capture the mouse to support scrolling, native selection needs Shift-drag.

## The costs of inline, and how to handle them

1. **You can't change anything once it's in `<Static>`.** No collapsing tool output, no editing earlier messages, no updating a spinner on an old item. Only move an item into `<Static>` when it's truly finished.

2. **Long streaming responses are the main trap.** Ink redraws the whole dynamic region on every frame. If the in-progress message grows taller than the terminal, you get flicker, duplicated lines and garbage in the scrollback. The fix is to **commit as you go**:
   - Split the streaming message into blocks: paragraphs, list items, closed code fences.
   - When a block is complete, push it onto the `<Static>` items array.
   - Keep only the unfinished tail block, plus the input box and status line, in the live area.
   - Cap the live area's height. If a single block gets too tall (say a huge code fence), show only its last N lines while it streams and commit the full block when it closes.

3. **Markdown re-parsing.** Partial markdown renders differently from the finished version: an unclosed fence, a half-written table. Committing at block boundaries means you only ever commit stable output, and the tail block is the only thing that can change.

4. **Resizing.** Whatever is already in scrollback, the terminal reflows itself. Plain text survives that fine, but borders, boxes and right-aligned elements break. Keep committed content mostly plain text with ANSI colors, and save the boxes for the live region, which Ink re-lays out.

5. **Throttle rendering.** Tokens can arrive hundreds of times a second. Batch them and re-render at roughly 30–60 fps, not on every chunk.

## When to use the alternate screen instead

Pick alt-screen if you need:

- multiple panes, like a conversation list sidebar or a split view with a file or diff
- switching between conversations within the app
- collapsing, expanding, editing or re-running earlier messages in place
- interactive elements inside history (buttons, foldable tool calls)

If you do go that way, be aware that Ink has no built-in scroll view or virtualization. You'd be measuring rendered heights and slicing the list yourself, plus writing your own scroll handling, search and copy. You'd probably also want to print the transcript to the normal screen on exit so it isn't lost.

## A middle ground

Stay inline for the main chat, and open alt-screen only for short full-screen moments: a conversation picker, a diff viewer, a settings screen. Enter it with `\x1b[?1049h` and leave with `\x1b[?1049l`, or render a separate Ink instance. When it closes, the user is back in their scrollback with nothing lost.

If you share how you're structuring the message and stream state, I can sketch the block-commit logic for it.
