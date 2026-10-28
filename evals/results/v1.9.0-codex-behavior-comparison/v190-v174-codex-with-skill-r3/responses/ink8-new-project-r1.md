For a new CLI, target **Ink 8.x + React 19.3+ + Node 24**, using ESM (`"type": "module"`).

The skill’s compatibility guidance is:

| Ink | React minimum | Node minimum |
|---|---|---|
| **8.x — recommended** | 19.3 | 22 |
| 7.x | 19.2 | 22 |
| 6.x — legacy bridge | 19 | 20 |

Node 22 remains an option; avoid starting on Node 20, which is end-of-life.

For terminal width, **use `useWindowSize()`**:

```tsx
import {Text, useWindowSize} from 'ink';

function App() {
  const {columns, rows} = useWindowSize();

  return <Text>{columns} columns × {rows} rows</Text>;
}
```

It updates on resize. In Ink 8, `useStdout().stdout` is typed as a generic stream, so `.columns` is no longer part of its typed API. The underlying TTY may still expose it at runtime, but use the size hook for layout and keep `useStdout()` for writing outside the live UI.