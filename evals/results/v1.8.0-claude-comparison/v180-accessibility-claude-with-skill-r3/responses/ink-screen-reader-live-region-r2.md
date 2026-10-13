## Why NVDA keeps re-reading everything

`INK_SCREEN_READER=true` changes what Ink draws. It does not change how Ink updates the screen. The screen-reader renderer prints flat text with no borders or color, and it replaces children with their `aria-label`. It still erases and rewrites the whole live region on every state change. The live region is everything that isn't inside `<Static>`.

So if the conversation history sits in the normal React tree:

1. Every spinner frame (often every ~80 ms) is a state change.
2. Each change makes Ink erase and rewrite the live region, including the full transcript.
3. NVDA sees the console text change and reads the new text aloud. The user hears the conversation again, plus spinner glyphs read one character at a time.

Streaming tokens into the live region causes the same problem, and so does any elapsed-time counter or token counter in a status line. Lowering `maxFps` or turning on `incrementalRendering` only reduces how often this happens. It doesn't stop the rewrites.

## What to change

**1. Move finished messages into `<Static>`.** `<Static>` writes each item once, above the live UI, and never redraws it. It ends up in normal scrollback and gets read once. Only append to the array: once an item has been written, editing it has no effect. A message that is still streaming therefore can't go into `<Static>` until it's complete.

**2. Keep the live region tiny.** In screen-reader mode it should hold only the input prompt and at most one status line.

**3. Stop all motion in screen-reader mode.** Replace the spinner with one static line such as `Assistant is responding…`. When the reply is done, append it to `<Static>` and the status line goes away. Remove ticking timers and counters too.

**4. Don't stream tokens live in screen-reader mode.** Buffer the reply and append it when it's complete. For long replies, you could append finished paragraphs as separate `<Static>` items instead.

**5. Make each line understandable when spoken:**
- Prefix lines with the speaker: `You:` and `Assistant:`. Start errors with `Error:` and say what to do next.
- Set `aria-hidden` on decorative glyphs and `aria-label` on meaningful icons.
- Arrow-key menus get re-read every time the highlight moves. Use numbered choices with a typed answer instead.
- Stay inline (no `alternateScreen`), leave the cursor at the prompt, and consider ringing the terminal bell when the app needs input, as Claude Code's screen-reader mode does.

Here's a sketch, branching on the hook (Gemini CLI's `--screen-reader` mode also uses a separate layout and a static spinner):

```tsx
import {Box, Static, Text, useIsScreenReaderEnabled} from 'ink';
import {Spinner} from '@inkjs/ui';

function Chat({messages, pending, draft}) {
  const sr = useIsScreenReaderEnabled();

  return (
    <>
      {/* Written once, read once; append-only */}
      <Static items={messages}>
        {m => (
          <Text key={m.id}>
            {m.role === 'user' ? 'You' : 'Assistant'}: {m.text}
          </Text>
        )}
      </Static>

      {pending &&
        (sr ? (
          <Text>Assistant is responding…</Text>
        ) : (
          <Box>
            <Spinner />
            <Text> {draft}</Text>
          </Box>
        ))}

      <Prompt />
    </>
  );
}
```

Even sighted users benefit from step 1, because Ink stops repainting the whole history on every token.

## How to check it

- Run with `render(<App />, {debug: true})` and `INK_SCREEN_READER=true`. Debug mode appends each frame instead of redrawing in place, so you can see how often frames happen. With nothing going on, no new frames should appear. While a reply is pending, you should see one `responding…` frame and then the final message.
- Add an ink-testing-library test with screen-reader mode on. Check that the transcript is never part of the live frame and that waiting produces no new frames.
- Then do a quick manual pass with NVDA to confirm it reads each message exactly once.

Ink won't turn this mode on by detecting a screen reader; it only happens through the env var or `isScreenReaderEnabled`. Document `INK_SCREEN_READER` (or your own `--screen-reader` flag), and consider saving it as a setting so users only have to turn it on once.
