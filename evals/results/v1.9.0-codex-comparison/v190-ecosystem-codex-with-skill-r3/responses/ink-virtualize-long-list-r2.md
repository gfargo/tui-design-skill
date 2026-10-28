**Virtualize the list: mount only the visible rows.** In Ink 8, `contentOffsetY` shifts and clips content; it doesn’t virtualize it. Yoga still lays out all 20,000 children, and Ink still paints them on each update.

Replace the full `.map()` with a slice:

```tsx
const height = Math.max(1, viewportRows); // available content rows
const maxTop = Math.max(0, entries.length - height);
const visibleTop = Math.max(0, Math.min(top, maxTop));

useInput((_input, key) => {
  if (key.downArrow) {
    setTop(t => Math.min(maxTop, Math.max(0, t) + 1));
  }
  if (key.upArrow) {
    setTop(t => Math.max(0, Math.min(t, maxTop) - 1));
  }
}, {isActive: isFocused});

return (
  <Box flexDirection="column" height={height} overflow="hidden">
    {entries.slice(visibleTop, visibleTop + height).map(entry => (
      <Text key={entry.id} wrap="truncate-end">
        {entry.message}
      </Text>
    ))}
  </Box>
);
```

Remove `contentOffsetY` from this viewport—the slice now controls scrolling.

Keep each entry to **one terminal line**, including flattening embedded newlines, so row indices match screen rows. If you need wrapped entries, virtualize by measured line heights instead. Recalculate viewport height on resize and clamp scrolling after filtering or deleting entries.

`React.memo` and `incrementalRendering` can help other costs, but the main fix is reducing mounted rows from 20,000 to roughly one screenful.