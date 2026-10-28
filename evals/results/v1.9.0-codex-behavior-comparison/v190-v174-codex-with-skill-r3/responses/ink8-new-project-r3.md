For a new CLI, target **Ink 8.x + React ≥19.3 + Node 24 LTS**, using ESM (`"type": "module"`). Ink 8’s minimum Node version is **22**; Node 20 is end-of-life.

Use **`useWindowSize()`** for terminal dimensions:

```tsx
import {Text, useWindowSize} from 'ink';

function App() {
  const {columns, rows} = useWindowSize();
  return <Text>{columns} × {rows}</Text>;
}
```

**`useStdout().stdout.columns` is no longer typed in Ink 8**, because its output stream is generic. An actual TTY stream may still expose it at runtime, but `useWindowSize()` is the supported API and updates on resize. Keep `useStdout()` for writing outside the live UI.

Source: the skill’s [TypeScript ecosystem reference](/Users/gfargo/dev/gfargo/tui-design-skill/.claude/worktrees/eloquent-ritchie-f2f1c8/plugins/tui-design/skills/tui-design/references/ecosystem-typescript.md).