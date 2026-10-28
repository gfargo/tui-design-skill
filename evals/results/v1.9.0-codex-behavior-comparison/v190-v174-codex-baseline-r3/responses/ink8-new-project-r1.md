For a new CLI today (October 28, 2026), target:

| Dependency | Version |
|---|---|
| Ink | **8.0.0** — current stable |
| React | **19.3.x** — Ink 8 requires ≥19.3 |
| Node.js | **22+** — Ink’s minimum |
| `@types/react` | **19.3.x**, if using TypeScript |

Use ESM (`"type": "module"`). These requirements come from [Ink’s package metadata](https://github.com/vadimdemedes/ink/blob/v8.0.0/package.json).

For terminal width, use **`useWindowSize()`**:

```tsx
import {Text, useWindowSize} from 'ink';

function App() {
  const {columns, rows} = useWindowSize();

  return <Text>{columns} columns × {rows} rows</Text>;
}
```

In Ink 8, `useStdout().stdout` is typed as `NodeJS.WritableStream`, so `.columns` and `.rows` are no longer available in its types. They may still exist at runtime on a TTY, but aren’t guaranteed for arbitrary streams. `useWindowSize()` also automatically re-renders on resize. See the [Ink 8 migration guide](https://github.com/vadimdemedes/ink/releases/tag/v8.0.0).