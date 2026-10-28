**Virtualize the list.** `overflow="hidden"` clips the output, and `contentOffsetY` shifts it, but all 20,000 entries still participate in React rendering and Ink’s layout work.

Mount only the entries visible in the viewport:

```tsx
// Assumes each entry occupies exactly one terminal row.
const visibleEntries = entries.slice(
  scrollOffset,
  scrollOffset + viewportHeight,
);

return (
  <Box flexDirection="column" height={viewportHeight} overflow="hidden">
    {visibleEntries.map(entry => (
      <Text key={entry.id} wrap="truncate">
        {entry.message}
      </Text>
    ))}
  </Box>
);
```

On arrow presses, update `scrollOffset`, clamped between `0` and `Math.max(0, entries.length - viewportHeight)`. Remove `contentOffsetY`: slicing now controls which rows appear.

Compute `viewportHeight` from the terminal height minus headers and footers, and update it on resize. If entries can wrap across multiple rows, use virtualization that tracks **terminal row heights**, rather than assuming one entry equals one row.

Memoization can help with expensive row formatting, but reducing the mounted list from 20,000 entries to roughly one screen is the main fix.