**Stop mounting all 20,000 rows. Mount only the rows that fit on screen.** `contentOffsetY` only moves and clips the content. Yoga still lays out all 20,000 children and Ink still paints them on every frame, so each arrow press costs 20,000 rows of work. Slice the array to the visible window, put it in a fixed-height box, and remove `overflow="hidden"` and `contentOffsetY` from the list. Those two props are fine for short content like a help panel, but not for a long list.

### The fix

```tsx
import React, {memo, useState} from 'react';
import {Box, Text, useInput, useWindowSize} from 'ink';

type Entry = {id: string; line: string};

const Row = memo(({line, selected}: {line: string; selected: boolean}) => (
  <Text wrap="truncate-end" inverse={selected}>{line}</Text>
));

const LogList = ({entries, isActive}: {entries: Entry[]; isActive: boolean}) => {
  const {rows} = useWindowSize();
  const height = Math.max(1, rows - 2);            // leave room for header/footer
  const margin = height < 12 ? 1 : 3;              // keep the next rows visible near the edge
  const [selected, setSelected] = useState(0);
  const [top, setTop] = useState(0);

  const move = (to: number) => {
    const next = Math.max(0, Math.min(entries.length - 1, to));
    setSelected(next);
    setTop(t => {
      if (next < t + margin) t = next - margin;
      if (next > t + height - 1 - margin) t = next - height + 1 + margin;
      return Math.max(0, Math.min(t, entries.length - height));
    });
  };

  useInput((input, key) => {
    if (key.downArrow || input === 'j') move(selected + 1);
    if (key.upArrow || input === 'k') move(selected - 1);
    if (key.pageDown) move(selected + height - 1);
    if (key.pageUp) move(selected - height + 1);
    if (key.home || input === 'g') move(0);
    if (key.end || input === 'G') move(entries.length - 1);
  }, {isActive});

  return (
    <Box flexDirection="column">
      <Box flexDirection="column" height={height}>
        {entries.slice(top, top + height).map((e, i) => (
          <Row key={e.id} line={e.line} selected={top + i === selected} />
        ))}
      </Box>
      <Text dimColor>{(selected + 1).toLocaleString()}/{entries.length.toLocaleString()}</Text>
    </Box>
  );
};
```

### What matters in it

1. **The slice.** At any time, only about `height` rows (around 40) are mounted, so each key press costs the same whether you have 200 entries or 2 million.
2. **One line per row.** The slice assumes each entry takes exactly one terminal line. With the default `wrap`, a long log line wraps, pushes the bottom rows out of the box, and breaks the scroll math. Use `wrap="truncate-end"` and show the full entry in a detail view or behind a wrap toggle (`w`).
3. **Memoized rows with stable keys.** `key={e.id}` and `memo` mean a single arrow press re-renders only the two rows whose selection changed. Don't key by index.
4. **`isActive` on `useInput`.** Every mounted `useInput` handler fires on every key. If another handler in the app (another pane, a dialog) is also active, your list moves when it shouldn't and work is wasted. `useFocus` alone doesn't stop this.
5. **Scroll margin and a position counter.** The selection stays 3 rows from the viewport edge, and the footer shows `4,213/20,000`. With 20k rows, the count tells the user where they are better than a scrollbar would.

### Other settings worth changing

- **`render(<App />, {alternateScreen: true, incrementalRendering: true})`.** By default Ink rewrites the whole live region every frame. With `incrementalRendering`, it rewrites only the lines that changed.
- **If the logs are still streaming in:**
  - Cap retained lines with a ring buffer and say when old lines were dropped.
  - Add follow mode: stay pinned to the bottom by default, pause on any upward movement, show a `▾ 37 new` badge, and re-pin on `G`.
  - Batch incoming lines (or use `useDeferredValue` with `concurrent: true`), and consider a lower `maxFps` than the default 30, so a burst of logs doesn't compete with key presses.
- **Don't use `<Static>` for this.** It prints lines permanently above the UI and never re-renders them. It works for append-only output you don't navigate, not for a list you scroll.
- **Keep file reading off the event loop.** If you load or parse the logs with `readFileSync` or a long synchronous loop, key presses queue behind it. Use `fs/promises` or a worker.

**If it's still slow after slicing**, profile it. Run with `node --cpu-prof`, then open the `.cpuprofile` file in Chrome DevTools or speedscope. The usual causes are:
- parent components re-rendering without memoization;
- a spinner that keeps animating and triggers constant redraws;
- filtering or sorting all 20k entries on every render instead of in `useMemo`.
