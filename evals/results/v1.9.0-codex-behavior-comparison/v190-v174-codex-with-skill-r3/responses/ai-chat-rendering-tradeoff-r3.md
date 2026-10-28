**Start inline if your main loop is “ask → read → follow up.” Choose the alternate screen if browsing and manipulating conversation history is central.** Streaming alone doesn’t require either buffer.

| Consideration | Inline + `<Static>` | Alternate screen |
|---|---|---|
| History | Native terminal scrollback, selection, search | You implement scrolling, search, and copying |
| After exit | Transcript remains visible | Previous shell screen returns |
| Earlier messages | Printed content is immutable | Can reflow, edit, collapse, or branch |
| Layout | Small live region beneath history | Stable composer, panes, overlays |
| Main risk | A growing streaming answer overwhelms the live region | Taking responsibility for the whole terminal experience |

For the straightforward chat client you described, I’d choose **inline, with completed content in `<Static>` and the unfinished response in ordinary live components**.

The critical detail: **don’t put a changing response into `<Static>`.** Once an item is printed, updates won’t repaint it.

Use this rendering model:

```text
<Static>  completed messages / finalized blocks
Live      unfinished response tail
Live      request status + composer
```

Batch token updates—roughly every 30–50 ms is a reasonable starting point. Keep the live region within the available terminal height. For long answers, commit finalized paragraphs or code blocks into `<Static>` and retain only the unfinished tail. Markdown makes this trickier: later tokens can change formatting, so define conservative commit boundaries and never revise already printed blocks.

Keep the conversation in your application’s data model, independently of what has been printed. Terminal scrollback is a viewing surface, not durable conversation storage.

A minimal layout, with the same single-column structure across widths:

```text
Wide terminal                         60-column split
You: Explain this function.            You: Explain this function.

Assistant:                            Assistant:
Completed explanation...              Completed explanation...
                                      wraps to available width.
[unfinished response tail]
                                      [unfinished response tail]
Streaming | Ctrl+C cancel             Streaming | Ctrl+C cancel
> follow-up draft                     > follow-up draft
```

At **80×24**, cap the composer and streaming tail so the controls remain visible. At **60 columns**, wrap prose, omit optional model/token metadata, and offer long code through a pager or export. Declare and test a smaller minimum—for example, 40×10—below which you show a resize message while preserving cancellation.

The clutter budget here is small: **zero borders, one speaker label per turn, no marker on every line, and one status/hint row**. That row consumes about 4% of a 24-row terminal.

Switch to the alternate screen when you need a pinned composer while independently scrolling history, message selection, branching, collapsible tool output, or persistent side panels. In Ink 7+, that’s supported through `render(<App />, {alternateScreen: true})`; it still requires your own history viewport and navigation.

For either choice, preserve partial text on cancellation or connection failure, provide a retry action, and ship a linear plain mode with answers on stdout and diagnostics on stderr. **Choose based on who should own history navigation: the terminal or your application.**