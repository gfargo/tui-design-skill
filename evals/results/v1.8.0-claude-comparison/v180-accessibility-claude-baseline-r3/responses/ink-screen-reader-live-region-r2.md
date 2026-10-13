I couldn't look at your code because the working directory is empty, so this is based on how Ink's screen-reader mode works rather than on your app. Check the specifics against your source.

## Why it happens

Setting `INK_SCREEN_READER=true` changes **what** Ink prints. It does not change **how** Ink updates the screen. In screen-reader mode Ink turns your tree into plain text, using `aria-label`, `aria-role` and `aria-state` and dropping anything marked `aria-hidden`. But every render still erases the whole live area and writes it again. NVDA in a terminal reads any new text that appears, so every repaint gets read out from the top.

Two things make this worse:

1. **The conversation is probably in the live area.** If past messages are rendered from state, like `messages.map(...)` inside a normal `<Box>`, they're part of every repaint. Anything that re-renders, such as a keystroke, a streamed token or a spinner tick, rewrites the whole history, and NVDA reads it all again.
2. **The spinner re-renders about 10 times a second.** Each tick repaints the live area, which re-reads everything in it. The spinner glyphs may also be read out on their own. Adding `aria-hidden` to the spinner removes the glyph from the output, but its timer still triggers the repaints. That's why "we hid it" usually doesn't fix this.

Streaming replies have the same problem, because each new token rewrites the partial message.

## What to change

**1. Move finished messages into `<Static>`.** Ink writes `<Static>` items once, above the live area, and never repaints them. This is the most important fix, and sighted users get faster rendering from it too.

```tsx
<>
  <Static items={completedMessages}>
    {m => <Message key={m.id} message={m} />}
  </Static>
  {/* live area: keep this as small as possible */}
  <Status />
  <Input />
</>
```

**2. Don't mount animated components in screen-reader mode.** Swap the spinner for static text that only changes when the state changes:

```tsx
const sr = useIsScreenReaderEnabled();

{busy && (sr
  ? <Text>Assistant is responding…</Text>
  : <Spinner />)}
```

Apply the same rule to anything else on a timer, like elapsed-time counters, clocks or progress bars. If it ticks, it causes a repaint.

**3. Don't stream token by token in screen-reader mode.** Either keep the reply hidden until it's complete and then add it to `<Static>`, or add it in sentence or paragraph chunks. Each chunk then gets read once and doesn't trigger a re-read.

**4. Keep the live area to just the input and a one-line status.** Then any repaint that does happen only re-reads a short line.

**5. Label things properly.** Put `aria-label` on things that are only visual, like the input prompt marker and role badges such as "You:" or "Assistant:". Use `aria-hidden` on decoration like borders and dividers.

**6. Optionally, throttle repaints.** If your Ink version has a render-rate option (`maxFps` in recent versions; check the Ink 8 docs), turning it down in screen-reader mode helps. It's no substitute for steps 1–3.

## Checking the fix

Run the app with `INK_SCREEN_READER=true` and pipe or record what it prints, for example with `script`. Each message should appear in the output exactly once, and the screen should stay still while the assistant is "thinking." Then confirm with NVDA, since terminal screen readers behave differently from each other.

If you share the chat layout component and the spinner, I can point to the exact changes.
