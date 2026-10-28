For a chat-first terminal client, I’d default to **an inline transcript with Ink’s `<Static>`**, with the streaming response rendered below it. Choose the alternate screen if you’re building a full-screen workspace with panes, transcript navigation, or extensive message editing.

The key distinction is who owns scrolling: the terminal or your application.

| | Inline with `<Static>` | Alternate screen |
|---|---|---|
| Transcript history | Native terminal scrollback | You implement scrolling and history |
| Copying and searching | Familiar terminal behavior | Depends on your UI and terminal |
| Streaming | Live response below committed history | Update a controlled viewport |
| Layout | Works well for a linear conversation | Better for panes and persistent panels |
| After exit | Transcript stays visible | Usually restores the previous screen |

For the inline approach, use this structure:

```text
<Static> completed messages </Static>
         current streaming response
         status / tool activity
         composer
```

Treat `<Static>` as an **append-only output boundary**. Keep the active response outside it while tokens arrive; when the response finishes, move it into the static history and remove the live version in the same render. Give committed items stable IDs.

The main caveat is **long streaming responses**. Once the live region exceeds the terminal height, cursor-based redraws can produce jumps, duplication, or flicker, depending on Ink’s version and rendering behavior. Test this early with long code blocks, terminal resizing, and multiline input. If necessary, commit stable, completed blocks as they stream and retain only a bounded live tail. Avoid committing arbitrary token chunks: Markdown formatting can change as more text arrives.

Alternate screen gives you more control, but it also makes you responsible for scroll anchoring, following new tokens, preserving the user’s position when they scroll up, selection behavior, and resize reflow.

**My recommendation:** start inline for a conversational CLI. Use alternate screen when navigating and manipulating the conversation becomes a central interaction, rather than just reading it and entering the next prompt.