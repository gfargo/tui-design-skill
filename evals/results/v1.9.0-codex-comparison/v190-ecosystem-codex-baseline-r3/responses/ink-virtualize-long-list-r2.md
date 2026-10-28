`overflow="hidden"` clips rendering; it doesn’t virtualize the list. All 20,000 entries still create React elements and participate in layout, so changing `contentOffsetY` remains expensive.

**Render only the visible rows**, plus a small overscan buffer. For single-line entries:

```jsx
const start = Math.max(0, scrollTop - 3);
const end = Math.min(entries.length, scrollTop + viewportHeight + 3);

return (
  <Box
    height={viewportHeight}
    flexDirection="column"
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

Keep `scrollTop` clamped to `0…Math.max(0, entries.length - viewportHeight)`. Now each arrow press updates only a viewport’s worth of rows.

If entries wrap across multiple lines, virtualize by **rendered line height**, using measured or cached row heights. Memoizing rows can help afterward, but reducing the mounted list is the main fix.