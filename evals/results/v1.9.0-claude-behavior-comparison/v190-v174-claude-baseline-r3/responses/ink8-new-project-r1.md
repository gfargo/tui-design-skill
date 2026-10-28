The working directory is empty, and I can't reach npm or GitHub from here. What follows is from memory, current up to about mid-2026. Before you pin versions, run `npm view ink version peerDependencies engines` to confirm.

## Versions

| | Target | Why |
|---|---|---|
| **Ink** | `^6` | Ink 6 is the current major version. It needs Node ≥ 20 and React ≥ 19. |
| **React** | `^19` | Ink 6 requires it as a peer dependency. React 18 only works with Ink 5. |
| **Node** | Set `engines` to `>=22`. Develop on Node 24 LTS. | Node 20 reached end of life in April 2026, so even though Ink accepts it, don't support it. Node 22 is in maintenance and Node 24 is Active LTS. Node 26 should be moving to LTS about now, so you can add it to CI. |

Ink and its dependencies are ESM-only, so put `"type": "module"` in package.json. If you use TypeScript, set `"module": "nodenext"`, `"jsx": "react-jsx"` and add `@types/react@^19`.

## `useStdout().stdout.columns`

Yes, that still works. `stdout` is the Node `WriteStream` that Ink is rendering to. But reading it directly has two problems:

1. **It doesn't update.** Your component reads the width once per render and won't re-render when the terminal is resized.
2. **It can be `undefined`.** When output is piped or running in CI, there's no TTY, so you need a fallback.

A small hook fixes both:

```tsx
import {useEffect, useState} from 'react';
import {useStdout} from 'ink';

export function useTerminalSize() {
  const {stdout} = useStdout();
  const read = () => ({columns: stdout.columns ?? 80, rows: stdout.rows ?? 24});
  const [size, setSize] = useState(read);

  useEffect(() => {
    const onResize = () => setSize(read());
    stdout.on('resize', onResize);
    return () => {
      stdout.off('resize', onResize);
    };
  }, [stdout]);

  return size;
}
```

Newer Ink 6.x minor releases may include a built-in hook for terminal dimensions. Check the Ink README or changelog for the version you install. If there is one, use it instead of this hook.

If you want, I can set up the project skeleton with package.json, tsconfig, an entry file with `render()`, and this hook.
