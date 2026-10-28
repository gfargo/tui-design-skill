**Virtualize the list: mount only the visible entries.** In Ink 8, `overflow="hidden"` and `contentOffsetY` shift and clip content; Yoga still lays out and Ink still paints all 20,000 children each frame.

Replace the full `.map()` with a slice, and let arrow keys change the starting index:

```tsx
const [top, setTop] = useState(0);

// height is the available content height, excluding header/footer/borders.
const maxTop = Math.max(0, entries.length - height);
const start = Math.min(top, maxTop);

useInput((_input, key) => {
  if (key.downArrow) setTop(Math.min(maxTop, start + 1));
  if (key.upArrow) setTop(Math.max(0, start - 1));
}, {isActive: isFocused});

return (
  <Box flexDirection="column" height={height} width={width}>
    {entries.slice(start, start + height).map(entry => (
      <Text key={entry.id} wrap="truncate-end">
        {entry.message}
      </Text>
    ))}
  </Box>
);
```

Keep each entry to **one terminal line** so the slice matches the viewport; normalize embedded newlines too. If you need wrapped entries, use virtualization that tracks each entry’s rendered height.

Recompute `height` on resize and clamp the starting index when data changes. At 80×24 or in a 60-column split, show fewer rows and truncate long messages, with full text available in a detail view.

Memoization and `incrementalRendering` can help afterward, but they don’t replace reducing the mounted list from 20,000 rows to roughly one screenful.