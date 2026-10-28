Use **Ink 8**, **React 19.3 or newer**, and **Node 22 or 24**. And no, don't read the width from `useStdout().stdout.columns`. Use `useWindowSize()` instead.

## Versions

| | Target | Why |
|---|---|---|
| **Ink** | `^8.0.0` | Current major (8.0.x, October 2026). |
| **React** | `^19.3.0` | Ink 8 requires React ≥ 19.3. Ink 7 only needed 19.2. |
| **Node** | `"engines": { "node": ">=22" }` | Ink 7 and 8 need Node 22 or newer, and Node 20 is end-of-life. Develop and run CI on Node 24 and also test on 22. |

Two things to settle on day one:

- **Use ESM.** Ink can't be loaded with `require('ink')` from CommonJS. Yoga, its layout engine, uses top-level await, so the call throws `ERR_REQUIRE_ASYNC_MODULE`. Set `"type": "module"` in `package.json`, or use `await import('ink')` or a bundler.
- **The rest of the stack needs Node 22 too:** chalk 6, commander 15 (needs 22.12+), execa 10 and listr2 11 (needs 22.13+). A floor of `>=22.13` covers all of them.

Only drop to Ink 6 (Node ≥ 20, React ≥ 19) if you must deploy somewhere that can't leave Node 20. You'd lose `useWindowSize`, `usePaste`, `alternateScreen` and `suspendTerminal`.

## Terminal width

Ink 8 no longer types `useStdout().stdout` as a TTY stream, so `stdout.columns` isn't in the types anymore. Even when it worked, it didn't trigger a re-render when the window was resized. Use `useWindowSize()`, which returns `{columns, rows}` and updates on resize:

```tsx
import {Box, Text, useWindowSize} from 'ink';

const App = () => {
  const {columns, rows} = useWindowSize();

  if (columns < 60 || rows < 15) {
    return <Text>Terminal too small: need 60×15, have {columns}×{rows}</Text>;
  }

  return columns >= 100 ? <TwoPane /> : <SinglePane />;
};
```

Keep `useStdout()` and `useStderr()` for their real job, which is writing lines above or outside the live UI. If you need the size of one particular box rather than the whole terminal, use `useBoxMetrics()`. In Ink 8 it also gives `clientWidth`/`clientHeight`, the size inside the border.

## Other Ink 8 changes that catch people

- `minWidth`/`maxWidth` only accept numbers now; percentages no longer work.
- Backspace arrives as `key.backspace` (since Ink 7), not `key.delete`.
- `useInput` no longer receives mouse or focus reports. If you want mouse support, you have to parse raw stdin yourself.
- For a full-screen app, use `render(<App />, {alternateScreen: true})`. Print any final summary after `await waitUntilExit()`, because output written during teardown is discarded.

If you tell me whether this is an inline prompt or a full-screen app, I can sketch the layout at 80×24 and in a 60-column split next.
