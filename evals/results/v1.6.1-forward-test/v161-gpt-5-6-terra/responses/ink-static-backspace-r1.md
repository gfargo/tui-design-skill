No—`<Static>` is for append-only output (logs/history). Its contents never re-render, so filtered rows, selection, and diff updates would become stale.

For a 50k-row selectable diff, implement a viewport:

- Keep the full filtered model in state/memoized data.
- Render only the visible slice based on `scrollOffset`, terminal height, and selection.
- Update that slice normally as the query changes; use deferred/debounced filtering if needed.

In Ink 7, Backspace is `key.backspace`:

```tsx
useInput((input, key) => {
  if (key.backspace) {
    setQuery(query => query.slice(0, -1));
  }
});
```

`key.delete` is the forward Delete key.
