I couldn't find any source files in the working directory, so this is based on how Ink's screen-reader mode works, not on your code. If you point me at the app I can check the specifics.

## Why it happens

`INK_SCREEN_READER=true` changes what Ink renders. It doesn't change how Ink updates the terminal.

- **Ink redraws the whole live area on every update.** Everything rendered outside `<Static>` is erased and written again whenever any state changes. Screen-reader mode replaces the box drawing with plain text and `aria-label`s, but the erase-and-rewrite still happens.
- **NVDA reads new terminal text as it appears.** It can't tell that a rewritten line is the same as the old one, so it reads it again.
- **A spinner updates many times a second.** Each update redraws the live area. If the conversation is part of that area, NVDA re-reads the conversation on every spinner frame, along with the spinner glyph. Streaming tokens cause the same problem: each token triggers a redraw.

So the screen-reader flag is working. The problem is that the conversation and the animations share one live area that redraws constantly.

## What to change

**1. Move finished messages into `<Static>`.** Ink writes `<Static>` items once, above the live area, and never redraws them. This is the most important fix.

```tsx
<>
  <Static items={completedMessages}>
    {m => <Message key={m.id} message={m} />}
  </Static>
  {/* live area: only the in-progress reply, status, and input */}
  <StreamingReply />
  <Status />
  <Input />
</>
```

**2. Turn off animation in screen-reader mode.** Use `useIsScreenReaderEnabled()`:

```tsx
const sr = useIsScreenReaderEnabled();
return sr
  ? <Text>Thinking…</Text>   // static text, changes only when the state changes
  : <Spinner />;
```

Also skip elapsed-time counters, progress bars and token counters in this mode. Anything that ticks will trigger re-reads.

**3. Don't stream tokens to screen-reader users.** When screen-reader mode is on, show "Responding…" while the reply is generated. Commit the full reply to `<Static>` once it's complete (or once per paragraph if replies are long). Otherwise NVDA gets a partial re-read on every token.

**4. Keep the live area as small as possible.** Ideally it holds just the status line and the input prompt. Mark decorative output with `aria-hidden` (borders, bullets, icons). Use concise `aria-label`s so labels like "Thinking" aren't followed by glyph noise.

**5. Change status text only when the state changes.** For example, go from "Thinking…" to "Response ready" to the input prompt. Don't rebuild the string on a timer, even if it ends up identical.

## How to check

Run with `INK_SCREEN_READER=true`, then capture stdout (for example `script`, or pipe through `cat -v`). Send one message and confirm two things:
- Each past message appears in the output exactly once.
- Nothing is written repeatedly while the app waits for a reply.

Then test with NVDA itself. Terminal behavior varies (Windows Terminal vs. conhost), so the raw output isn't a full substitute.
