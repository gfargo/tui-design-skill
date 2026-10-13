## Why NVDA keeps re-reading

The cause is how Ink's screen-reader mode works, plus how NVDA notices new text.

1. **Ink's screen-reader renderer still repaints.** `INK_SCREEN_READER=true` (or `isScreenReaderEnabled: true`) prints linear text: no borders, no color, and `aria-label` in place of children. But it still **erases and rewrites the whole live region every time anything changes**. The flag changes what gets drawn, not how often it gets redrawn.
2. **NVDA finds new text by comparing the terminal's contents.** Windows Terminal also reports text as it's written. So every time Ink rewrites the region, NVDA sees "new" text and reads it.

That explains both complaints:

- **The conversation is re-read** because the transcript is probably part of the live tree. Then any change rewrites the whole conversation, whether it's a streamed token, a status update or a single keystroke in the input box.
- **The spinner is re-read** because each frame is a state change. That means a full live-region rewrite many times a second, and each new frame character is announced. Elapsed-time counters and token meters cause the same problem.

The flag gives you clean text. You still have to stop the repainting yourself.

## What to change

Follow one rule in screen-reader mode: **add new lines; don't redraw old ones.**

**1. Move finished messages into `<Static>`.** `<Static>` prints each item once, above the live UI, and never re-renders it. That's what stops the conversation from being re-read. Only add a message to it once the message is complete, because Static output can't be changed afterwards.

**2. Keep the live region to about one line.** In screen-reader mode it should hold only the prompt or input, plus at most one status line. Remove the header, footer, key hints, token counter, timer and model badge, or print them once into Static.

**3. Don't stream tokens into the live region.** Buffer the assistant's reply and add it to Static when it finishes, or one paragraph at a time if replies are long. Streaming character by character means rewriting and announcing constantly.

**4. Replace the spinner with a single line of text.** Print something like `Assistant is thinking…` once, then the result. Don't leave a frozen spinner frame, and drop any per-second timers. In Gemini CLI's `--screen-reader` mode, a static spinner and a separate layout do this job.

**5. Label every line.** Start each message with the speaker (`You:`, `Assistant:`), and start status lines with `error:` or `warning:`. Listeners then know what a line is before hearing it.

**6. Other fixes for this mode:**
- Don't use `alternateScreen`, so output stays in scrollback where users can review it.
- Leave the cursor visible on the input. Screen readers and magnifiers follow the cursor.
- Replace arrow-key menus with numbered choices and a typed answer. Otherwise NVDA re-reads the menu every time the highlight moves.
- Show tables as `Header: value` lines, and remove box drawing from rendered markdown or code blocks.
- Ring the terminal bell when the app needs input. Claude Code's screen-reader mode does this.

### Sketch

```tsx
import {Box, Static, Text, useIsScreenReaderEnabled} from 'ink';

function Chat({messages, pending, busy}: Props) {
  const sr = useIsScreenReaderEnabled();

  return (
    <>
      {/* Finished messages are printed once and never repainted */}
      <Static items={messages}>
        {m => (
          <Text key={m.id}>
            {m.role === 'user' ? 'You: ' : 'Assistant: '}
            {m.text}
          </Text>
        )}
      </Static>

      {sr ? (
        // Screen-reader live region: one static status line plus the input
        <Box flexDirection="column">
          {busy && <Text>Assistant is thinking…</Text>}
          <PromptInput />
        </Box>
      ) : (
        // Sighted live region: streaming text, spinner, footer, etc.
        <Box flexDirection="column">
          {busy && <StreamingReply text={pending} />}
          <PromptInput />
          <Footer />
        </Box>
      )}
    </>
  );
}
```

In screen-reader mode, the reply goes into `messages` (and so into `<Static>`) only once it's finished. Don't render `pending` in that mode.

`<Static>` also helps sighted users, because Ink no longer redraws the whole history on every token. You'll probably want it in both modes.

## Two caveats

- **Nothing detects a screen reader.** `useIsScreenReaderEnabled()` only reports the flag. Document the env var, and add a `--screen-reader` flag or a saved setting so users can turn it on once. Also turn this linear mode on automatically when stdout isn't a TTY.
- **The live region is never completely silent.** Ink still rewrites the input line on each keystroke, so keep that region as small as possible.

To check the fix, run with `render(<App />, {debug: true})`. It prints each frame separately, so you can see exactly what gets rewritten on each update. Then test a real conversation with NVDA in Windows Terminal. Aim for each message being read once and nothing announced while the assistant is working except the single "thinking" line.
