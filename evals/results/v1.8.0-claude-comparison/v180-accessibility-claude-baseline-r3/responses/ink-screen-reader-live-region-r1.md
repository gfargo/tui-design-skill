I couldn't check your code because the working directory has no source files. This answer is based on how Ink's screen-reader mode works, not on your app. If you share the chat and spinner components, I can point to specific lines.

## Why it happens

`INK_SCREEN_READER=true` changes what Ink outputs. It replaces visual layout with plain text and uses your `aria-*` props. It does **not** change when Ink redraws.

Ink still re-renders the whole dynamic part of the screen whenever any state changes. NVDA's console support reads text as it is written to the terminal. So every repaint looks like new content and gets announced again.

In a chat app, two things usually cause this:

1. **The spinner.** A spinner updates state every ~80ms. Each tick redraws everything outside `<Static>`. If the conversation history is in that redrawn area, NVDA re-reads it on every tick. Setting `aria-hidden` on the spinner only hides its frames. The timer keeps running and keeps forcing redraws.
2. **Streaming tokens.** Updating state for each token or chunk redraws the in-progress message each time, so NVDA reads it again from the start.

## What to change

**1. Put finished messages in `<Static>`.** Ink writes `<Static>` items once and never redraws them, so NVDA reads each message once. Only the in-progress reply and the input box should be in the live area.

```tsx
<>
  <Static items={completedMessages}>
    {m => <Message key={m.id} message={m} />}
  </Static>
  {pending && <PendingReply ... />}
  <Prompt ... />
</>
```

**2. Turn off the spinner animation in screen-reader mode.** Hiding it isn't enough; the timer itself has to stop.

```tsx
import {useIsScreenReaderEnabled, Text} from 'ink';

function Busy() {
  const sr = useIsScreenReaderEnabled();
  if (sr) return <Text aria-role="status">Assistant is thinking…</Text>;
  return <Spinner />; // the interval only runs in this branch
}
```

Apply the same rule to anything else that ticks: elapsed-time counters, clocks and progress dots.

**3. Don't stream token by token in screen-reader mode.** Either show "thinking…" and add the full reply to `<Static>` when it's done, or add text in sentence or paragraph chunks. The goal is that each piece of text is written to the terminal once.

**4. Reduce noise elsewhere:**
- Put `aria-hidden` on decorative borders, dividers and icons.
- Use `aria-label` on elements whose visual text doesn't read well, such as `aria-label="You said:"` in place of a `❯` glyph.
- Keep role labels short and consistent ("You:", "Assistant:") so users can tell turns apart.

**5. Test with NVDA itself.** Run with `INK_SCREEN_READER=true` in Windows Terminal and conhost. Check three things: the old conversation is never re-announced while the model is working, each reply is read once, and typing in the prompt doesn't trigger re-reads.

Steps 1 and 2 will probably fix most of the complaints. Step 3 addresses the rest.
