## Why it happens

`INK_SCREEN_READER=true` only changes how Ink formats output. It does not change how Ink updates the screen. In that mode Ink prints plain linear text with no borders or color, and it uses `aria-label` in place of a component's children. On every state change, though, it still erases and rewrites the whole live region, which is everything not inside `<Static>`.

NVDA treats the rewritten text as new output and reads it again. So in your app:

1. **The conversation is re-read** because the message history is in the live region. Each new message, each streamed token, and each keystroke in the input causes Ink to rewrite the whole transcript.
2. **The spinner is re-read** because it re-renders on a timer, about 10 times a second. Each frame is a change, so the live region is rewritten that often even when nothing important happened. Spinner characters are also read out one symbol at a time.

The env var formats the output for a screen reader, but it doesn't make updates screen-reader friendly. Nothing in Ink detects a screen reader, either. `useIsScreenReaderEnabled()` only reports whether the flag is set, so the app has to change its own behavior when it is.

## What to change

The rule is: add new lines, and don't rewrite old ones.

**1. Move finished messages into `<Static>`.** `<Static>` prints each item once above the live UI and never re-renders it. NVDA hears each message once, and it stays in normal scrollback.

**2. Keep the live region tiny.** In screen-reader mode it should contain only the input line and, while a reply is pending, one short status line.

**3. Don't stream tokens into the live region in this mode.** Collect the reply and add it to `<Static>` when it's complete. If replies are long, add it a paragraph at a time.

**4. Replace the spinner with a static line.** Show `Working…` once, then the final result. Also stop any elapsed-time counters or other timers that update every tick. Gemini CLI's `--screen-reader` mode does the same thing: a separate layout with a non-animated spinner.

```tsx
import {Static, Box, Text, useIsScreenReaderEnabled} from 'ink';
import {Spinner} from '@inkjs/ui';

function Chat({messages, streaming, busy}) {
  const sr = useIsScreenReaderEnabled();
  const done = messages.filter(m => m.complete);

  return (
    <>
      <Static items={done}>
        {m => <Text key={m.id}>{m.author}: {m.text}</Text>}
      </Static>

      {/* Live region: keep it to a line or two in SR mode */}
      {!sr && streaming && <Text>{streaming.author}: {streaming.text}</Text>}
      {busy && (sr ? <Text>Working…</Text> : <Spinner label="Thinking" />)}
      <PromptInput />
    </>
  );
}
```

**5. Related fixes for screen-reader mode:**
- **Label each line by speaker.** Start every message with `You:` or `Assistant:` so listeners know who's talking before they hear the text. Start errors with `error:`.
- **Don't use `alternateScreen`.** Output should stay in scrollback so users can review it.
- **Keep the terminal cursor on the input line.** NVDA follows the cursor, so don't hide it.
- **Use numbered choices instead of arrow-key menus.** An arrow-key menu is re-read every time the highlight moves. Print a numbered list and read the typed answer.
- **Remove decoration.** Drop box drawing, ASCII art, and aligned tables. Write table rows as `Header: value` lines.
- **Signal when the app needs input.** Ring the terminal bell, as Claude Code's screen-reader mode does.

**6. Know the limits of `<Static>`.** Content inside it can't be updated. If a message changes after it's printed, keep it in the live region until it's final, or add the change as a new line (`Tool result: …`). Don't edit the old one.

**7. Make the mode easy to turn on and keep on.** Keep the env var, and add a `--screen-reader` flag and a saved config setting. Don't try to detect NVDA.

## How to check it

- Run with `render(<App />, {debug: true})` and the env var set. Debug mode prints every frame instead of updating in place, so you can see exactly what gets rewritten. While the app is idle there should be no new frames, and old messages should never appear in a frame again.
- Add an ink-testing-library test with screen-reader mode on: send a message, wait for the reply, then assert that `lastFrame()` doesn't contain earlier messages and that the frame count stays the same while idle.
- Finally, test once with NVDA in Windows Terminal.
