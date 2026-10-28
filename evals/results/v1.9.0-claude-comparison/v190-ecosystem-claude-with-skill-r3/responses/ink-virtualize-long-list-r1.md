The problem is `contentOffsetY` itself. It only shifts and clips content that is already rendered. Yoga still lays out all 20,000 rows and Ink still paints all of them, then clips the result to the viewport. So each arrow press costs 20,000 rows of work.

**What to change:** stop mounting the whole list. Keep a `top` offset in state and render only `entries.slice(top, top + height)` inside a fixed-height box. Each keypress then costs about one screen of rows, however long the log gets. Remove `overflow="hidden"` and `contentOffsetY` from this list. They're fine for a modest amount of content, but not for a collection this size.

```tsx
import React, {useState} from 'react';
import {Box, Text, useInput} from 'ink';

type Entry = {id: string; line: string};

export function LogList({entries, height, width, isActive}: {
  entries: Entry[]; height: number; width: number; isActive: boolean;
}) {
  const [selected, setSelected] = useState(0);
  const [top, setTop] = useState(0);

  const move = (to: number) => {
    const next = Math.max(0, Math.min(entries.length - 1, to));
    const margin = height < 12 ? 1 : 3; // keep the next rows visible before the edge
    setSelected(next);
    setTop(t => {
      if (next < t + margin) t = next - margin;
      else if (next > t + height - 1 - margin) t = next - height + 1 + margin;
      return Math.max(0, Math.min(t, entries.length - height));
    });
  };

  useInput((input, key) => {
    if (key.downArrow || input === 'j') move(selected + 1);
    if (key.upArrow || input === 'k') move(selected - 1);
    if (key.pageDown) move(selected + height - 1);
    if (key.pageUp) move(selected - (height - 1));
    if (key.home || input === 'g') move(0);
    if (key.end || input === 'G') move(entries.length - 1);
  }, {isActive});

  return (
    <Box flexDirection="column" width={width} height={height}>
      {entries.slice(top, top + height).map((entry, i) => (
        <Text key={entry.id} wrap="truncate-end" inverse={top + i === selected}>
          {entry.line}
        </Text>
      ))}
    </Box>
  );
}
```

**Make sure the slice math holds:**

- **One entry must be exactly one line.** `wrap="truncate-end"` handles that. With the default wrapping, a long log line takes several rows, the slice overflows the box, and the selection drifts. Show the full entry in a detail view or behind a wrap toggle (`w`) instead.
- **Use a numeric height.** Get it from `useWindowSize().rows` minus your header and footer, or measure the parent with `useBoxMetrics()` and pass `clientHeight` down.
- **Gate `useInput` with `isActive`.** Every mounted `useInput` hook runs on every key. If other panels also have unguarded handlers, one arrow press runs all of them.
- **Do expensive work once, not on every render.** Wrap filtering, formatting and colorizing of the 20k entries in `useMemo` keyed on the data and the filter. Otherwise you've just moved the slowness from layout into your own render function.

**UX details you get almost for free once you're windowing:**

- **Show the position**, e.g. `4,213/20,000` in the footer or panel title. Once you stop scrolling a real container, this count is the user's main sense of where they are in the log.
- **Use a stable key.** Key rows by entry ID, as above, not by array index. If entries keep arriving, also track the selection by ID so it doesn't jump when lines are added.
- **If the log is live, add follow mode.** Open pinned to the bottom. Any upward movement pauses following and shows a `▾ 37 new` badge, and `G` or `F` re-pins. Keep the most recent 10k–100k lines in a ring buffer and say when old lines were dropped.
- **Don't use `<Static>` for this.** It works for finalized, append-only output, but it doesn't virtualize a list that can be selected or filtered.
