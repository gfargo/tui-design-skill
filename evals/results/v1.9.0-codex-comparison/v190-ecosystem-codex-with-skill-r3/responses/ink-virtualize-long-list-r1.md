**Virtualize the list by slicing before rendering.** Ink 8’s `contentOffsetY` shifts and clips content, but Yoga still lays out—and Ink still paints—all 20,000 mounted rows on each frame.

Keep a scroll index and mount only the visible entries:

```tsx
function LogList({entries, height, width, isActive = true}) {
  const [offset, setOffset] = useState(0);
  const maxTop = Math.max(0, entries.length - height);
  const top = Math.min(Math.max(0, offset), maxTop);

  useInput((_input, key) => {
    const delta = key.downArrow ? 1 : key.upArrow ? -1 : 0;

    if (delta) {
      setOffset(Math.max(0, Math.min(maxTop, top + delta)));
    }
  }, {isActive});

  return (
    <Box flexDirection="column" height={height} width={width}>
      {entries.slice(top, top + height).map(entry => (
        <Text key={entry.id} wrap="truncate-end">
          {entry.message}
        </Text>
      ))}
    </Box>
  );
}
```

Use the viewport’s available **content height**, excluding borders, padding, and other UI. Recalculate it on resize. Remove `contentOffsetY` from this list.

Keep each entry to one terminal line: truncate and normalize embedded newlines. Wrapped entries require virtualization based on measured line heights instead.

With a 20-row viewport, this mounts about 20 rows instead of 20,000. Memoization and `incrementalRendering` can help afterward, but they don’t replace virtualization. Gate `useInput` when another pane or dialog has focus.