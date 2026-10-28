Render only the rows that fit on screen, not all 20,000.

`overflow="hidden"` only clips what gets drawn. Ink still builds all 20,000 children in React and runs Yoga layout on every one of them. Each arrow press changes the scroll offset, which triggers a re-render, so you pay for 20,000 rows to show about 30. Setting the offset doesn't skip that work.

### Fix: render a slice of the rows

```tsx
import React, {useState, memo} from 'react';
import {Box, Text, useInput, useStdout} from 'ink';

type Entry = {id: string; level: string; message: string};

const Row = memo(({entry, selected}: {entry: Entry; selected: boolean}) => (
  <Text inverse={selected} wrap="truncate-end">
    {entry.level.padEnd(5)} {entry.message}
  </Text>
));

export function LogList({entries}: {entries: Entry[]}) {
  const {stdout} = useStdout();
  const height = Math.max(1, (stdout?.rows ?? 24) - 2); // leave room for header/footer
  const [cursor, setCursor] = useState(0);
  const [top, setTop] = useState(0);

  useInput((_input, key) => {
    let next = cursor;
    if (key.upArrow) next = Math.max(0, cursor - 1);
    if (key.downArrow) next = Math.min(entries.length - 1, cursor + 1);
    if (key.pageUp) next = Math.max(0, cursor - height);
    if (key.pageDown) next = Math.min(entries.length - 1, cursor + height);
    if (next === cursor) return;

    setCursor(next);
    // Keep the cursor inside the window
    if (next < top) setTop(next);
    else if (next >= top + height) setTop(next - height + 1);
  });

  const visible = entries.slice(top, top + height);

  return (
    <Box flexDirection="column" height={height}>
      {visible.map((entry, i) => (
        <Row key={entry.id} entry={entry} selected={top + i === cursor} />
      ))}
    </Box>
  );
}
```

### Why this works

- **Fixed row height:** `wrap="truncate-end"` keeps every entry to one line, so "visible rows" is just `height`. If entries can wrap to several lines, the windowing math gets much harder. Truncate in the list and show the full entry in a detail pane.
- **Only visible rows exist:** React and Yoga handle about 30 nodes no matter how long the log gets. You can also drop `overflow="hidden"` and `contentOffsetY`, since the slice does the scrolling.
- **`memo` plus stable keys:** when the cursor moves, only the two rows whose `selected` value changed re-render.
- **Keep the array stable:** if you filter or format `entries`, wrap that in `useMemo`. Otherwise you rebuild 20,000 items on every keypress.

### Other things to check

- **Logs still streaming in:** if new lines arrive quickly, batch them (for example, flush every 50–100 ms) so you don't call `setState` once per line.
- **Terminal resizes:** `stdout.rows` isn't reactive. Listen for `stdout.on('resize', …)` and store the row count in state.
- **No scrolling needed:** if you only need to show output as it arrives, Ink's `<Static>` writes each item once and never re-renders it.

If you share your current component, I can adapt this to it.
