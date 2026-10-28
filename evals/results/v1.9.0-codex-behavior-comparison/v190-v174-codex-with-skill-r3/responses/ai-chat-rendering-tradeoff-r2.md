**Start inline if your main loop is “ask → read streamed answer → ask again.”** Choose the alternate screen when navigating and manipulating conversation history becomes a core part of the product. Streaming alone doesn’t require either buffer.

| | Inline + `<Static>` | Alternate screen |
|---|---|---|
| History | Terminal scrollback; familiar selection and copying | App owns scrolling, search, selection, and copying |
| After exit | Transcript remains visible | Previous shell screen returns; transcript needs persistence/export |
| Past messages | Committed output cannot be revised | Can reflow, collapse tools, edit, branch, and rerender |
| Layout | Works best with a small live region | Stable viewport and composer; room for panels |
| Main cost | Long streaming answers and immutable history | Building navigation and restoring terminal state reliably |

For inline Ink, **keep the streaming response out of `<Static>` until it is finalized**:

```text
<Static>  completed, immutable turns
live UI   current streaming response + status + composer
```

Batch token updates into frames instead of rendering every token. On completion, move the answer into the static transcript and clear the live response in the same state transition. Preserve interrupted text with an explicit `Interrupted` or `Connection lost` label.

The main trap is an answer that grows taller than the terminal. An unbounded live region can produce expensive redraws and awkward scrolling. Either commit finalized, immutable blocks progressively—accepting that later Markdown cannot revise them—or cap the live preview and provide a way to inspect the full answer. If that compromise undermines reading, **use the alternate screen**.

I’d switch to alternate screen once requirements include conversation search, branching, editable earlier turns, collapsible tool output, or frequent browsing while generation continues. Implement follow mode explicitly: scrolling upward pauses following without stopping generation; show `12 new lines`; jumping to the end resumes following. Keep printable shortcuts inactive while the composer owns input.

Keep the initial layout single-column at every width:

```text
Wide terminal                           60-column split
Assistant                               Assistant
The response streams here...            The response wraps here...
                                        across available columns.

Generating · Ctrl+C cancel              Generating · Ctrl+C cancel
> Ask a follow-up                       > Ask a follow-up
Enter send · Alt+Enter newline           Enter send · Alt+Enter newline
```

At 80×24, give the transcript priority and bound composer growth. At 60 columns, wrap prose and hide optional metadata. For a proposed interactive minimum of 40×8, show a resize message below that and keep cancellation and exit working.

This layout has zero border nesting, one status cue, and no repeated per-line markers; the live controls occupy about three rows with a one-line composer. Avoid boxed messages and repeating model names or timestamps on every line.

For either approach, persist conversation data separately from rendered output. Provide a linear `--no-tui` mode with answers on stdout and diagnostics on stderr; inline repainting alone does not make streaming accessible.

**For the client you described, I’d ship inline first—with a deliberate policy for answers taller than the screen.** Choose alternate screen from the outset if conversation navigation is already central to your intended experience.