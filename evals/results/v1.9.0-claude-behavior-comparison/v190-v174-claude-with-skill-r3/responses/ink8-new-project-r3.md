**Target Ink 8, React 19.3 or later, and Node 24.** Don't read the width from `useStdout().stdout.columns`. Use `useWindowSize()` instead.

## Versions

| | Target | Why |
|---|---|---|
| **Ink** | `^8.0` (current major, Oct 2026) | Adds scroll offsets (`contentOffsetX/Y`), `clientWidth/Height` in `useBoxMetrics()`, and keeps Ink 7's `useWindowSize`, `usePaste`, `suspendTerminal` and `alternateScreen` |
| **React** | `^19.3` | Ink 8 needs React 19.3 or later. Ink 7 needed 19.2. |
| **Node** | 24, with `engines: ">=22"` | Ink 7 and 8 need Node 22 or later. Node 20 is end-of-life. Of the two lines Ink supports, Node 24 has longer support. Check the Node release schedule for the current LTS line before you set `engines`. |

Only use Ink 6 (Node 20+, React 19+) as a temporary bridge if a deployment really can't leave Node 20. For a new project it's the wrong choice.

**Make the project ESM from the start** (`"type": "module"`). Newer Node versions let CommonJS `require()` most ESM-only packages, but Ink is an exception. Its Yoga layout engine uses top-level await, so `require('ink')` throws `ERR_REQUIRE_ASYNC_MODULE`. If you're stuck with CommonJS, use `await import('ink')` or a bundler.

The other current majors (chalk 6, commander 15, execa 10, listr2 11) also need Node 22 or later. Commander 15 needs 22.12 and listr2 11 needs 22.13, so Node 24 covers all of them.

## Terminal width

**No.** Ink 8 types the streams from `useStdout()` generically, so `stdout.columns` no longer type-checks. This is one of the three common breaks when upgrading to Ink 8. On a real TTY the property may still exist at runtime, but reading it during render was always fragile because it doesn't re-render your component on resize.

Use `useWindowSize()` instead. It updates on resize:

```tsx
import {Box, Text, useWindowSize} from 'ink';

const Layout = () => {
  const {columns, rows} = useWindowSize();

  if (columns < 60 || rows < 15) {
    return <Text>Terminal too small ({columns}×{rows}). Need at least 60×15.</Text>;
  }

  const showSidebar = columns >= 100;
  return (
    <Box height={rows}>
      {showSidebar && <Box width={30}><Text>Sidebar</Text></Box>}
      <Box flexGrow={1}><Text>Main</Text></Box>
    </Box>
  );
};
```

For the size of one panel rather than the whole terminal, use `useBoxMetrics()`. In Ink 8 its `clientWidth` and `clientHeight` give the space inside the borders, which is what you need for truncation and for deciding how many list rows to render.

Keep `useStdout()` for its actual job: `write()` prints permanent lines above the live UI.

## Other Ink 7/8 changes to know from day one
- **Backspace:** check `key.backspace`. Older examples check `key.delete`, which no longer catches Backspace.
- **`minWidth`/`maxWidth`:** these take numbers only in Ink 8, not percentages.
- **Mouse:** `useInput` no longer receives mouse or focus reports, so mouse support means parsing raw stdin.
- **Exiting:** await `waitUntilExit()` before printing a final summary or calling `process.exit()`. With `alternateScreen: true`, anything written during teardown is discarded.

The default stack I'd pair with this is Ink, @inkjs/ui, zustand, commander and ink-testing-library. @inkjs/ui and ink-testing-library are unmaintained but still work with Ink 8.
