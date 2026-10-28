**Stop mounting all 20,000 rows. Mount only the rows that fit on screen.**

## Why it's slow

`contentOffsetY` on an `overflow="hidden"` Box only moves and clips the content. It doesn't skip any work. On every arrow press, React reconciles all 20,000 children, Yoga lays out all 20,000 rows, and Ink paints them all before clipping to the visible area. So each keypress costs 20,000 rows of work, and only about 30 of them end up on screen.

## The fix: virtualize by slicing

Keep the full array in state, but render only `entries.slice(top, top + height)` inside a fixed-height Box. Each keypress then costs about one screen of rows, whatever the size of the log.

```tsx
import React, {memo, useState} from 'react';
import {Box, Text, useFocus, useInput, useWindowSize} from 'ink';

type Entry = {id: number; line: string};

const Row = memo(({line, selected}: {line: string; selected: boolean}) => (
  <Text wrap="truncate-end" inverse={selected}>{line}</Text>
));

const LogView = ({entries}: {entries: Entry[]}) => {
  const {rows} = useWindowSize();
  const height = Math.max(1, rows - 2);          // leave room for a status line
  const {isFocused} = useFocus({autoFocus: true});
  const [selected, setSelected] = useState(0);

  useInput((_input, key) => {
    const last = entries.length - 1;
    if (key.downArrow) setSelected(i => Math.min(last, i + 1));
    if (key.upArrow) setSelected(i => Math.max(0, i - 1));
    if (key.pageDown) setSelected(i => Math.min(last, i + height));
    if (key.pageUp) setSelected(i => Math.max(0, i - height));
    if (key.home) setSelected(0);
    if (key.end) setSelected(last);
  }, {isActive: isFocused});

  const top = Math.max(0, Math.min(selected - Math.floor(height / 2), entries.length - height));

  return (
    <Box flexDirection="column">
      <Box flexDirection="column" height={height}>
        {entries.slice(top, top + height).map((e, i) => (
          <Row key={e.id} line={e.line} selected={top + i === selected} />
        ))}
      </Box>
      <Text dimColor>{selected + 1}/{entries.length}</Text>
    </Box>
  );
};
```

## Things that keep it fast and correct

- **Keep every row to one line.** The slice math assumes one row per entry. Ink's default `wrap` lets a long log line take several lines, which pushes rows out of the box. Use `wrap="truncate-end"` and put the full text in a detail view, or add a wrap toggle (`w`) that is off by default for columnar or JSON logs.
- **Use stable keys and memoized rows.** Keying by the entry's id and wrapping rows in `memo` means a scroll step only remounts the row entering and the row leaving. Only the two rows whose highlight changed re-render.
- **Gate `useInput` with `isActive`.** Every mounted `useInput` handler runs on every key unless it's gated. If other panes or a dialog also listen, the list keeps moving behind them, and you do extra work on each press.
- **Don't fall back to `<Static>`.** It's only for finished, append-only output. It can't scroll back, select, or filter, so it won't work for a selectable log view.

## If the log is live

Treat streaming entries as a follow mode:
- **Following:** pinned to the bottom by default.
- **Paused:** any upward movement stops following and holds the view still. Show a `▾ 37 new` counter, and let `G` or `F` re-pin to the bottom.
- **Cap the buffer:** keep something like the last 10k–100k lines and say when older ones were dropped.

To keep live updates cheap, batch incoming lines (`useDeferredValue` with `render(<App />, {concurrent: true})`, or a short debounce). Ink 8's `incrementalRendering: true` and a lower `maxFps` also cut redraw work.

## Checking it

`node --cpu-prof` produces a profile that shows the drop in per-keypress layout time. React DevTools won't help here, because Ink doesn't support its profiler. In tests, render with ink-testing-library and press `End` on a 20,000-entry fixture. Then assert that the last entry is visible and that no frame is taller than the terminal.
