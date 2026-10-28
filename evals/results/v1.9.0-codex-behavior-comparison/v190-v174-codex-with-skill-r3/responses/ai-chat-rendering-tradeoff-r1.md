**Start inline with `<Static>` for completed content and a bounded live region for the streaming response.** For a client whose main loop is “ask → read → follow up,” native terminal scrollback, selection, and shell context are valuable. Streaming alone doesn’t justify the alternate screen.

Choose the alternate screen if you’re building a workspace where users routinely search history, switch conversations, edit previous messages, expand tool calls, or navigate persistent panes.

| Concern | Inline + `<Static>` | Alternate screen |
|---|---|---|
| Read/copy previous output | Native terminal scrollback and selection | App must provide history navigation; selection varies |
| Transcript after exit | Remains in scrollback | Screen disappears; persist/export separately |
| Search, collapse, edit old messages | Limited: printed content is permanent | Fully controlled by the app |
| Fixed composer and panels | Awkward as live output grows | Natural |
| Implementation burden | Streaming boundaries and overflow | Scrolling, follow mode, search, virtualization |

**The key Ink constraint: `<Static>` is append-only.** Don’t put a message there while its text is still changing.

Use this rendering structure:

```text
<Static>  immutable transcript blocks
live      unfinished response / active tool status
live      composer + contextual hints
```

Keep the full conversation in your data model; `<Static>` is an output mechanism, not storage.

For long responses, don’t let the mutable response grow beyond the available terminal height. Either commit genuinely stable blocks incrementally—keeping an unfinished Markdown block live—or accept that this requirement pushes you toward an alternate-screen viewport. Committing whole responses only at completion works poorly when one answer spans several screens. Batch token updates to a modest frame rate, and ensure the live-to-static handoff prints each block exactly once.

A minimal inline layout can stay the same across widths:

```text
Wide (~100 columns)                      Narrow (60 columns)
You                                     You
Explain the retry policy.                Explain the retry policy.

Assistant                               Assistant
Retry transient failures with…           Retry transient failures
                                        with…
Streaming · Ctrl+C cancel               Streaming · Ctrl+C cancel
> Follow-up…                            > Follow-up…
```

At **80×24**, reserve space for the composer and status, and cap the mutable response to the remaining rows. At **60 columns**, wrap prose, omit optional model/token metadata, and keep one column. Below your declared usable minimum—say 40×10—show a clear “terminal too small” state and offer plain output.

Keep chrome sparse: **zero enclosing borders, one speaker label per message, one streaming indicator**. Remove per-line bullets, repeated timestamps, and duplicate spinner/status signals.

If you choose alternate screen, make upward scrolling pause following without stopping generation; show “new content” and an explicit jump-to-latest action. Keep those navigation keys out of text-entry mode. Also provide plain streaming output for pipes and accessibility, and restore terminal modes on every exit.

**My recommendation for the client you described: inline first. Move to alternate screen when navigating and manipulating the conversation becomes a core workflow.**