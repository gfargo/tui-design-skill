I read the skill's guidance on Ink, screen buffers, and streaming. Here's my answer.

## Recommendation: stay inline, with `<Static>` for finished output and a small live region

A chat transcript is append-only history, and that's the case inline mode handles best. Your users get the terminal's own scrollback, search (Cmd+F), text selection, tmux copy mode, and a transcript that's still there after they quit. With the alternate screen you'd have to build each of those yourself, and in the terminal people tend to dislike the home-made versions.

The catch is that inline only works if you keep the live region small.

### The rule that makes inline work

Ink redraws the whole live region on every frame. Once a growing answer is taller than the screen, its top scrolls into scrollback, and Ink can no longer erase or redraw that part. You end up with duplicated or torn text. Avoid that like this:

- **Move streamed text into `<Static>` in pieces as it arrives.** Each time a paragraph ends or a code fence closes, move that block into `<Static>`. Only the unfinished tail stays live. Don't wait for the whole message to finish.
- **Limit how tall the live region can get:** the streaming tail, a one-line status, and the input box. If the tail gets close to the screen height, move it to `<Static>` anyway.
- **Keep token updates cheap:** use `incrementalRendering: true` (Ink 8), the default `maxFps` of 30 or lower, and batch incoming tokens. `useDeferredValue` only fully works with `render(<App />, {concurrent: true})`.

```
┌─ wide (120 cols) ────────────────────────────────────────────────────────┐
  › how do I debounce in Ink?                         ← <Static> (scrollback)
  ◆ Use useDeferredValue, or batch tokens at ~30fps.  ← <Static>
    ```ts                                             ← <Static> (fence closed)
    const v = useDeferredValue(text)
    ```
  ◆ For append-only logs, also prefer <Stat▍          ← live tail (streaming)
  ⠋ streaming · sonnet-5.5 · 1.2k tok · Esc cancel    ← live status
  ─────────────────────────────────────────────────
  > _                                                 ← live input
└──────────────────────────────────────────────────────────────────────────┘

┌─ 60-col tmux split ──────────────────────┐
  › how do I debounce in Ink?
  ◆ Use useDeferredValue, or batch
    tokens at ~30fps.
  ◆ For append-only logs, also pref▍
  ⠋ streaming · Esc cancel
  ────────────────────────────────
  > _
└──────────────────────────────────────────┘
```

**Clutter audit:** no borders around messages. A role glyph (`›` for you, `◆` for the assistant) plus a color marks who's speaking. That's two signals for one fact, which is enough. The only rule line is the one above the input. That keeps almost every cell for content.

**At 60 columns:** the status line drops the model name and token count first, and prose wraps. Inline mode has no "terminal too small" state. The one real cost at narrow widths: text already in `<Static>` stays wrapped at the width it was drawn at, so widening the terminal won't reflow old messages. That's acceptable for a chat log.

### When the alternate screen is the better choice

Switch if your design needs to **change history after it's printed.** `<Static>` never re-renders, so inline can't do these:

- collapsing or expanding tool output, or showing and hiding thinking blocks after the fact
- editing a past message or branching the conversation at it
- a sidebar with a list of conversations, or several sessions in tabs
- scrolling inside the app, with a selection cursor over messages

If you need any of these, use `render(<App />, {alternateScreen: true})` and plan to build what the terminal was giving you for free:

- a scrolling message view that only renders the rows on screen. `contentOffsetY` alone still lays out every row.
- follow mode: stay pinned to the bottom while streaming, stop following when the user scrolls up, show a `▾ 37 new` indicator, and jump back with `G`.
- search and copy (OSC 52)
- mouse-wheel scrolling, which means parsing raw stdin, because Ink 8 drops mouse reports
- printing the transcript or a summary after `await waitUntilExit()`, since the alternate screen disappears on exit

### A middle path

Stay inline, and add a key that opens the full transcript in a pager:

```ts
await suspendTerminal(async () => runPager(transcriptPath)); // e.g. less -R
```

This gives users a full-screen view of long history without you writing a scroll view. Ink restores the terminal and redraws when the pager exits.

### Things to plan for in either mode

- **Ctrl+C:** set `exitOnCtrlC: false`. The first press cancels the stream through an `AbortController`, the second quits with exit code 130. Esc can cancel too.
- **Input:** use `usePaste` so pasting multiple lines doesn't send the message. Shift+Enter only reaches the app when the terminal supports the kitty keyboard protocol, so always accept Ctrl+J for a newline as well.
- **Keep the network off the render path:** stream with async fetch and an `AbortSignal`. Write debug output to stderr or a file, never to stdout.
- **Plain and scripted use:** add a `--print` / non-TTY mode that writes the answer as plain text to stdout. Inline with `<Static>` already suits Ink's screen-reader mode, which asks for exactly this split: finished output in `<Static>` and a small live part.

**Bottom line:** if your transcript is append-only, go inline with `<Static>`, move text into it at paragraph and code-block boundaries, and keep the live region to a few lines. Choose the alternate screen only if you plan to change past messages after they're printed or add side panels.
