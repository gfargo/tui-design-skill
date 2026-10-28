The working directory is empty, so this is based on how Ink works in general, not on your code.

**The problem:** `overflow="hidden"` only clips what gets drawn. All 20,000 rows still exist as React elements and Yoga layout nodes. Each arrow press changes the offset, so React reconciles all 20,000 children, Yoga lays out all of them, and then Ink throws away all but about 30 lines. Most of the work in every frame is wasted.

**The fix: only render the rows that fit on screen.** Store the scroll position as a number and render a `slice` of the array:

```tsx
import React, {useState, memo} from 'react';
import {Box, Text, useInput, useStdout} from 'ink';

type Entry = {id: string; level: string; message: string};

const Row = memo(({entry, selected}: {entry: Entry; selected: boolean}) => (
  <Text inverse={selected} wrap="truncate-end">
    {entry.level.padEnd(5)} {entry.message}
  </Text>
));

export function LogView({entries}: {entries: Entry[]}) {
  const {stdout} = useStdout();
  const height = Math.max(1, (stdout?.rows ?? 24) - 2); // leave room for header/footer
  const [cursor, setCursor] = useState(0);
  const [top, setTop] = useState(0);

  useInput((_input, key) => {
    let next = cursor;
    if (key.upArrow) next = Math.max(0, cursor - 1);
    else if (key.downArrow) next = Math.min(entries.length - 1, cursor + 1);
    else if (key.pageUp) next = Math.max(0, cursor - height);
    else if (key.pageDown) next = Math.min(entries.length - 1, cursor + height);
    else return;

    setCursor(next);
    // Keep the cursor inside the viewport
    setTop(t => (next < t ? next : next >= t + height ? next - height + 1 : t));
  });

  const visible = entries.slice(top, top + height);

  return (
    <Box flexDirection="column" height={height}>
      {visible.map((e, i) => (
        <Row key={e.id} entry={e} selected={top + i === cursor} />
      ))}
    </Box>
  );
}
```

Now each keypress renders about `height` rows, whether the list has 20 entries or 20 million.

**Other things that matter:**

1. **One row = one line.** Use `wrap="truncate-end"` (or truncate the text yourself) so every entry is exactly one line tall. If entries wrap to different heights, you can't map the scroll position to a slice without measuring each one.
2. **Use a stable `key` and `memo` the rows.** That way, moving the cursor only re-renders the two rows whose `selected` value changed.
3. **Don't format text during render.** Build the timestamp, padding and colour strings once when an entry arrives, not on every frame.
4. **Hold incoming logs outside React state if they arrive quickly.** If new entries stream in while the user scrolls, keep them in a ref or external store and flush to state on a timer (e.g. every 100 ms). Otherwise every new line triggers a render.
5. **Handle terminal resizes.** Listen for `stdout.on('resize', …)` and update the height so the slice stays correct.
6. **If you only need a tail view, use `<Static>`.** If the log never needs to scroll back interactively, Ink's `<Static>` writes each item once and never re-renders it. It can't scroll, though, so it only fits an append-only view.

I'm not certain `contentOffsetY` is part of Ink 8's API, and I couldn't check your code. Whatever prop you're using, though, clipping a fully rendered list is slow for the reason above. Rendering a slice is the standard fix, and it works on any Ink version.
