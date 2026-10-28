For a general-purpose terminal chat client, I’d default to **an inline transcript with Ink’s `<Static>`**, keeping the streaming response in a live region below it. Choose the alternate screen if your product needs to behave like a full-screen workspace.

The deciding factor is **who owns scrolling: the terminal or your app**.

| | Inline + `<Static>` | Alternate screen |
|---|---|---|
| Transcript scrolling | Native terminal scrollback | You implement scrolling and history |
| Copying and searching | Familiar terminal behavior | Depends on your UI and terminal |
| After exit | Conversation stays visible | Usually returns to the previous screen |
| Layout | Good for sequential conversation | Good for panes, navigation, and persistent UI |
| Rendering cost | Committed transcript stops rerendering | You manage the visible viewport |

For inline rendering, use this lifecycle:

1. Render completed messages in `<Static>`.
2. Render the current streaming response outside `<Static>`.
3. When it finishes, move it into the static transcript and clear the live response in the same state update.

**Keep the live region bounded.** A streaming response that grows taller than the terminal is where inline rendering becomes difficult: cursor movement and clearing can produce flicker, duplicate output, or scrollback artifacts. Long answers and expanding tool output deserve particular attention. You can progressively commit stable blocks, but Markdown constructs such as code fences and tables make that more complicated.

Also, `<Static>` commits output rather than providing a transcript viewport. Previously printed messages are effectively immutable; resize reflow is largely the terminal’s responsibility.

I’d choose the **alternate screen from the start** if users need to browse old messages while generation continues, edit earlier turns, expand tool results, or work with sidebars and multiple sessions. Those features benefit from an app-owned viewport enough to justify implementing scrolling, selection behavior, and resize handling.

For a conversational CLI, inline is the stronger default. For a terminal application centered on navigating conversation history, use the alternate screen.