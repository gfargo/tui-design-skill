**Go inline with `<Static>`.** A chat transcript only ever grows at the bottom, and the terminal's own scrollback already does that job well. The alternate screen is worth it only if you need things inline can't do (listed below).

## Why inline fits a chat client

- **Scrolling, search, and copy work for free.** The mouse wheel, `Cmd+F`, text selection and tmux copy-mode all work on the transcript. On the alternate screen you'd have to rebuild each of these. Turning on mouse capture to get wheel scrolling also breaks normal text selection.
- **The conversation stays after you quit.** Users can scroll back to an answer after exiting, or paste it into the next command. The alternate screen has no scrollback, so when the app exits the whole conversation disappears from the terminal.
- **No virtualization.** Lines committed to `<Static>` are written once and never re-render. The terminal holds the history, so long sessions don't make React work harder.
- **Better accessibility.** Linear output with speaker labels is what screen readers handle well. Ink's screen-reader mode tells you to move finished output into `<Static>` and keep the live part small, which is this design anyway.

## What inline costs you

Once a message is in `<Static>`, it's just terminal text. So:

- **No reflow on resize.** Old messages keep the wrapping they had when printed.
- **No editing past messages:** no collapsing a long tool output, re-theming, or highlighting the selected message.
- **No persistent side panes.** A conversation list or context panel can't sit next to the transcript.

If any of those is core to your product, use the alternate screen with `render(<App />, {alternateScreen: true})` (Ink 7+). That means you also own scrolling, virtualization (Ink 8's `contentOffsetY` plus `useBoxMetrics()` for the viewport), in-app search and copy. That's the "an app you live in" shape, where you'd build an IDE-like layout.

## The rule that makes inline work: keep the live region short

Ink erases and redraws the live region (everything outside `<Static>`) on each update. If a streaming reply grows taller than the terminal, the top of it scrolls off where Ink can't erase it, and you get duplicated or torn output. So don't keep the whole in-progress reply in the live region:

- **Commit finished blocks during streaming.** When a paragraph ends or a code fence closes, append that block to the `<Static>` items. Only the unfinished block stays live.
- **Keep a code block live until its closing fence arrives**, so syntax highlighting never runs on half a block.
- **Throttle repaints.** Ink 6.7+ uses synchronized updates. Also batch tokens with `useDeferredValue` (fully works only with `concurrent: true`) or a ~30–50 ms debounce. On Ink 8, `incrementalRendering: true` and a lower `maxFps` cut churn further.
- **Treat `<Static>` as append-only.** Give each committed block a stable key, and never edit an item after it's committed, because it won't re-render.

## Layout

Wide (100+ cols):
```
you  How do I debounce in React?
                                                  ← committed (<Static>)
ai   Use a ref-held timer and clear it on each call:
     ```ts
     const t = useRef<NodeJS.Timeout>();
     ```
     The cleanup in useEffect matters because…   ← live: current block only
─────────────────────────────────────────────────────────────────────────
› ▌                                                ← input
 claude-sonnet-5-5 · streaming · Esc stop · Ctrl+C quit         1.2k tok
```

Floor (60 cols, tmux split):
```
you  How do I debounce in React?
ai   Use a ref-held timer and clear it on each
     call:
     ```ts
     const t = useRef<NodeJS.Timeout>();
     ```
     The cleanup in useEffect matters because…
────────────────────────────────────────────────────────────
› ▌
 streaming · Esc stop                               1.2k tok
```

At 60 columns, text wraps at the indent, and the status line drops the model name first, then the token count. Inline output is linear, so there's no real "too small" state. Just make sure the live region (input, status, current block) fits within about 24 rows.

## Clutter audit

- **Borders:** none around messages. One rule above the input is the only chrome.
- **Speaker signals:** the text prefix (`you`/`ai`) plus at most one color. Don't add a box, an icon and a background as well. The text label keeps it readable under `NO_COLOR` and screen readers.
- **Repeated markers:** don't put a timestamp on every message. If you want times, put them on turn boundaries or behind a toggle.

## Other details

- **Ctrl+C:** the first press cancels the stream and keeps the partial reply (commit it with a `[stopped]` marker). The second press, when nothing is running, quits.
- **Exit output:** anything printed during teardown is lost. Print any final summary (e.g. `Saved session → ~/.chat/2026-10-27.md`) after `await waitUntilExit()`.
- **Opening the transcript in an external program:** if you later want "open the whole transcript in a pager," do it with `suspendTerminal(() => spawn('less', …))` rather than switching your whole app to the alternate screen. Users who want review tools then get one, and the default stays inline.

On "the way Claude Code does it": I'm going on your description there; I didn't look into Claude Code's internals.
