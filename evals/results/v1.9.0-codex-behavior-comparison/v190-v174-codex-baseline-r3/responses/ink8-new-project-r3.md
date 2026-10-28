For a new CLI today, target **Ink 8, React 19.3+, and Node.js 22+**. With TypeScript, use **`@types/react` 19.3+** too. These are Ink 8’s declared requirements; configure the project for ESM. [Package requirements](https://github.com/vadimdemedes/ink/blob/v8.0.0/package.json)

For terminal width, use **`useWindowSize()`**:

```tsx
import {Text, useWindowSize} from 'ink';

function App() {
  const {columns, rows} = useWindowSize();
  return <Text>{columns} × {rows}</Text>;
}
```

In Ink 8, `useStdout().stdout` is typed as `NodeJS.WritableStream`, so `.columns` and `.rows` are no longer available in its types. They may still exist at runtime for a TTY, but aren’t guaranteed. `useWindowSize()` also automatically re-renders on resize. [Ink 8 migration guide](https://github.com/vadimdemedes/ink/releases/tag/v8.0.0)