For a general-purpose terminal chat client, I’d start with **an inline transcript using Ink’s `<Static>`**, with the streaming response rendered beneath it. Use the alternate screen if you want a full-screen workspace with panes, transcript navigation, and persistent controls.

The main tradeoff is who owns scrolling: the terminal or your application.

| | Inline + `<Static>` | Alternate screen |
|---|---|---|
| Transcript history | Native terminal scrollback | You implement scrolling and history |
| Selection and copying | Usually natural | Depends on terminal and mouse handling |
| After quitting | Conversation stays visible | Previous terminal screen is restored |
| Layout | Best for a transcript above a prompt | Best for panes, menus, and inspectors |
| Earlier messages | Treat committed output as immutable | Can redraw or edit anything |

**Streaming doesn’t require the alternate screen.** With Ink, keep two regions:

- `<Static>` for completed messages, with stable IDs.
- A normal live region for the current response, status, and input.

When the response finishes, move it into the committed transcript and clear the live response in the same state update. Don’t append every token to `<Static>`: committed output cannot be revised, and Markdown formatting often changes as more text arrives.

The main inline pitfall is a long streaming response. Once the live region exceeds the terminal’s height, redraws and scrolling can become awkward. Prototype that case early, along with terminal resizing and large pasted input. If necessary, commit stable blocks as they finish and keep only the unfinished tail live; that requires more careful Markdown handling.

My recommendation: **choose inline for a conversational CLI that fits into a shell workflow; choose alternate screen for an application people will navigate inside.** Neither is inherently better for streaming.