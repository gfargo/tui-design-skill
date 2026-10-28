For a new CLI, target **Ink 8 + React 19.3 + Node 24**, using ESM.

| Dependency | Target | Minimum for Ink 8 |
|---|---|---|
| Ink | 8.0.x | — |
| React | 19.3+ | 19.3 |
| Node.js | 24 LTS | 22 |

Node 20 is end-of-life; use Ink 6 only as a compatibility bridge if you must support it.

For terminal width, **use `useWindowSize()`**:

```tsx
import {Text, useWindowSize} from 'ink';

function App() {
  const {columns, rows} = useWindowSize();
  return <Text>{columns} × {rows}</Text>;
}
```

It updates on resize. In Ink 8, `useStdout().stdout` is typed as a generic stream, so `.columns` is no longer available in its type. A real TTY stream may still expose it at runtime, but use the sizing hook for layout and keep `useStdout()` for writing outside the live UI.