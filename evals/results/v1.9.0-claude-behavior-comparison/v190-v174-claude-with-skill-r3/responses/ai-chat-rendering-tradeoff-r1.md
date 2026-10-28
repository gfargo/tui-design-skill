I've read the skill's guidance on Ink, inline vs. alternate screen, and the Claude Code / Copilot CLI case study. Here's my recommendation.

## Recommendation: start inline with `<Static>`, and design the transcript so you can move it to the alternate screen later

Inline is the simpler starting point, and it gives you the terminal's own scrollback, search and copy without building them. One correction first: "the way Claude Code does it" now covers two approaches. Claude Code's classic renderer is inline with `<Static>`. Its fullscreen renderer uses the alternate screen with a virtualized transcript, and it has been the default for new users since May 6, 2026 (`/tui` switches between them). Copilot CLI is alternate-screen only, and Gemini CLI defaults to inline. Both approaches are in production, and each costs something different.

| | Inline + `<Static>` | Alternate screen + virtualized transcript |
|---|---|---|
| You get for free | Native scrollback, terminal search, copy/select, history left after exit | A stable layout, flat memory, no flicker however long the session runs |
| Main cost | Long streaming sessions can flicker and jump the scroll position, and memory grows with the transcript | You must rebuild search, copy and exporting the transcript to scrollback, and you still need an inline fallback |
| Accessibility | Works with screen readers | Claude Code switches back to its classic inline renderer in screen-reader mode |

**When to switch:** stay inline until users report flicker, scroll jumps or memory growth in long sessions. Then add an alternate-screen mode and ship it with search, copy, scrollback export and the inline fallback. If you keep the transcript as a plain data model (`Turn[]`) separate from the renderer, the switch is a new view, not a rewrite.

## Making inline work while streaming

The usual mistake is letting the reply that's still streaming grow without limit in Ink's live region (the part below `<Static>` that Ink redraws). Keep that region small:

```tsx
const App = () => {
  const [done, setDone] = useState<Turn[]>([]);         // finalized: never re-renders
  const [streaming, setStreaming] = useState<string | null>(null);
  const tail = useDeferredValue(streaming);             // coalesce token bursts

  return (
    <>
      <Static items={done}>{turn => <TurnView key={turn.id} turn={turn} />}</Static>
      {tail !== null && <Text>{tail}</Text>}
      <Prompt />
    </>
  );
};

render(<App />, {exitOnCtrlC: false, concurrent: true, incrementalRendering: true});
```

- **Move finished blocks into `<Static>` during the stream.** When a paragraph or code fence closes, append it to `done`. The live region then holds only the unfinished block, so it never gets taller than the screen.
- **Only finished content goes in `<Static>`.** It never re-renders, so collapsible tool output, live token counts and "thinking…" indicators belong in the live region until they're final. Putting changing content in `<Static>`, or leaving finished content out of it, is a common Ink performance problem.
- **Limit redraws.** `useDeferredValue` only fully works with `concurrent: true`. Ink 8's `incrementalRendering: true` rewrites only the changed part of each line, and lowering `maxFps` (default 30) cuts churn further. Since Ink 6.7, synchronized updates prevent most tearing.
- **Ctrl+C should cancel first, then quit.** Pass `exitOnCtrlC: false` and handle Ctrl+C in an always-active `useInput`: the first press aborts the stream's `AbortController`, the second exits with code 130.
- **Handle paste.** Use `usePaste` so a multi-line paste arrives as one chunk and its newlines aren't treated as Enter.
- **Keep stdout clean.** Ink owns stdout, so send logs and traces to stderr or a file. Direct `process.stdout.write` calls and child processes with inherited stdio are what corrupt the screen.
- **Resize:** lines already in `<Static>` are in scrollback and were wrapped at the old width. Only the live region re-lays out on resize. That's acceptable, but don't promise that old turns will reflow.
- **If you add the alternate screen:** `render(<App />, {alternateScreen: true})` (Ink 7+) is ignored when stdout is piped or in CI, and anything printed during teardown is discarded. Print any exit summary after `await waitUntilExit()`.

## Layout at 100 columns and at a 60-column tmux split

```
100 cols                                                   60 cols
› how do I parse TOML in Rust?                             › how do I parse TOML in Rust?
                                                           
Use the `toml` crate with serde:                           Use the `toml` crate with
                                                           serde:
  #[derive(Deserialize)] struct Config { … }                 #[derive(Deserialize)] str…
                                                           
› and with comments preserved?                             › and with comments preserved?
                                                           
For round-tripping use `toml_edit`, which keeps▍           For round-tripping use
                                                           `toml_edit`, which keeps▍
╭──────────────────────────────────────────────────────╮   ╭──────────────────────────╮
│ > _                                                  │   │ > _                      │
╰──────────────────────────────────────────────────────╯   ╰──────────────────────────╯
 streaming · esc cancel        sonnet-5.5 · 4.2k tok        streaming · esc cancel
```

- **Floor (60 columns, 80×24):** with a single column, nothing has to hide except the status line. At 60 columns drop the model and token count, and keep the state and the cancel hint. Prose wraps. Code blocks truncate with `…` rather than wrapping, because wrapped code is misleading, and you can offer a copy or expand action for the full text. Below about 40×10, show a plain "terminal too small" message instead of a broken input box.
- **Clutter audit:**
  - Borders: one, around the input only. Don't box each message: with inline rendering, every border ends up in the user's scrollback and in anything they copy.
  - Role markers: one `›` per user turn, not a label on every line. Assistant text needs no prefix, since its position already identifies it.
  - Streaming state: shown by the cursor `▍` and the word "streaming", which is two signals. Don't add a spinner as a third.

**Tests:** unit-test the stream → `done` flushing logic without a terminal. Snapshot frames with `ink-testing-library` at 80×24 and 60 columns, using CJK and emoji in the replies. Add one PTY test with `node-pty` for Ctrl+C cancel-then-quit and for paste.
