`overflow="hidden"` clips the output, but **all 20,000 entries still participate in rendering and layout**. Changing `contentOffsetY` doesn’t virtualize the list.

Render only the visible entries, plus a small overscan buffer. For single-line entries:

```tsx
const viewportRows = 20;
const overscan = 3;
const [scrollTop, setScrollTop] = useState(0);

useInput((_, key) => {
  const delta = key.downArrow ? 1 : key.upArrow ? -1 : 0;

  if (delta) {
    setScrollTop(top =>
      Math.max(0, Math.min(
        Math.max(0, entries.length - viewportRows),
        top + delta,
      )),
    );
  }
});

const start = Math.max(0, scrollTop - overscan);
const end = Math.min(
  entries.length,
  scrollTop + viewportRows + overscan,
);

return (
  <Box
    flexDirection="column"
    height={viewportRows}
    overflow="hidden"
    contentOffsetY={-(scrollTop - start)}
  >
    {entries.slice(start, end).map(entry => (
      <Text key={entry.id} wrap="truncate">
        {entry.message}
      </Text>
    ))}
  </Box>
);
```

Now Ink lays out roughly 26 entries per arrow press instead of 20,000. Keep row keys stable, and memoize expensive row components if needed.

If entries wrap onto multiple terminal lines, virtualize by **line height**, not entry count: either enforce single-line rows or track row heights and cumulative offsets. Recalculate those heights when terminal width changes.