The fix is to **render only the rows that fit on screen**, not all 20,000 with the extras clipped.

## Why it's slow

`overflow="hidden"` hides rows visually, but Ink still does all the work for them. On every keypress:

1. React reconciles 20,000 `<Text>` elements.
2. Yoga computes layout for all 20,000 nodes.
3. Ink builds the output and clips it to the visible area.

Moving the offset changes what's visible, but that full pipeline still runs on every arrow press. Clipping only saves the final paint, which is the cheap part.

## The fix: a windowed list

Keep the scroll position in state and slice the array to the visible height:

```tsx
import {Box, Text, useInput, useStdout} from 'ink';
import {useState, memo} from 'react';

const Row = memo(({entry, selected}: {entry: LogEntry; selected: boolean}) => (
  <Text inverse={selected} wrap="truncate">
    {entry.time} {entry.level} {entry.message}
  </Text>
));

function LogList({entries}: {entries: LogEntry[]}) {
  const {stdout} = useStdout();
  const height = Math.max(1, stdout.rows - 2); // leave room for header/footer
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
        <Row key={top + i} entry={entry} selected={top + i === cursor} />
      ))}
    </Box>
  );
}
```

That cuts the per-keypress work from about 20,000 nodes to about 40.

## Details that matter

- **One terminal line per row.** `wrap="truncate"` makes each entry exactly one line, so "visible rows = terminal height" holds. If entries wrap to several lines, the slice math breaks, and you'd need per-row heights (much more complex). For logs, truncating and showing the full entry in a detail pane is usually better.
- **Use stable keys.** Use an entry ID if you have one. Index-based keys like `top + i` work too. Don't key by position within the slice (`i` alone), or React will re-render every row on each scroll.
- **Handle resize.** `stdout.rows` changes when the terminal is resized. Re-read it on the `resize` event, or use a hook that does, and clamp `top`.
- **`memo` on rows** stops unchanged rows from re-rendering when only the cursor moves.
- **Don't use `<Static>` here.** It's meant for append-only output that never changes. It won't help with a scrollable, selectable list.

If the log is still growing while you view it, keep entries in a ref or an external store and only trigger a re-render when the visible slice is affected. Otherwise every new line re-renders the list too.

I didn't find any source files in the working directory, so this is general advice. If you share your component, I can adapt it to your code, including how you're using `contentOffsetY` now.
