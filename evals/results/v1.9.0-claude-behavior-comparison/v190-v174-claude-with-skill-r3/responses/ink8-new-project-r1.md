**Target Ink 8 (8.0.x), React 19.3 or newer, and Node 22 or 24.** And no, don't read the width from `useStdout().stdout.columns` anymore. Use `useWindowSize()`.

### Versions

| | Target | Why |
|---|---|---|
| **Node** | 22 or 24 | Node 20 is end-of-life. Ink 7 and 8 require Node 22 or newer, and so do the current majors of the rest of the stack (chalk 6, commander 15 needs ≥ 22.12, listr2 11 needs ≥ 22.13, execa 10). |
| **Ink** | 8.0.x (current major, October 2026) | It has `useWindowSize`, `usePaste`, `alternateScreen`, `suspendTerminal` and `incrementalRendering`. |
| **React** | ≥ 19.3 | Ink 8 requires it (Ink 7 needed 19.2). |

Ink 6 (Node ≥ 20, React ≥ 19) is only worth it as a short-term bridge if you have to deploy somewhere that can't leave Node 20. That shouldn't apply to a new project.

**Use ESM from the start.** `require('ink')` throws `ERR_REQUIRE_ASYNC_MODULE` because Yoga uses top-level await. Other ESM-only packages like chalk and commander work through `require()` on Node 22.12+, but Ink doesn't. Set `"type": "module"` in package.json. If some part of the project has to stay CommonJS, load Ink with `await import('ink')` or bundle it.

A suggested default stack: **ink + @inkjs/ui + zustand + commander + ink-testing-library**. @inkjs/ui and ink-testing-library haven't had releases in a while, but both work with Ink 8.

### Terminal width

Ink 8 types the `useStdout()` and `useStderr()` streams generically, so `stdout.columns` is no longer typed. Use `useStdout()` only for writing output outside the live UI, and get the size like this:

```tsx
import {useWindowSize, Text} from 'ink';

function Layout() {
  const {columns, rows} = useWindowSize(); // updates on resize
  if (columns < 60) return <Text>Terminal too small — need 60 columns</Text>;
  return columns >= 100 ? <TwoPane /> : <SinglePane />;
}
```

To get the size of a particular box instead of the whole terminal, use `useBoxMetrics()`. In Ink 8 it also returns `clientWidth`/`clientHeight`, which is the space inside the borders.

### Other Ink 8 changes to know before porting old code or examples
- Percentage values for `minWidth` and `maxWidth` no longer work. Use plain numbers.
- `useInput` now drops mouse, focus and cursor-position reports instead of passing them through as text. If you want mouse support, you have to parse raw stdin yourself.
- Backspace shows up as `key.backspace` (this changed in Ink 7). Older snippets that check `key.delete` will silently break.
- In development, use `node --watch` or `nodemon --no-stdin`. Plain nodemon breaks arrow keys.
- Ink takes about 150–250 ms to draw its first frame. Make `--version` and shell completions skip Ink entirely.

If you tell me what the CLI does, I can help decide whether it should run inline or full-screen, and sketch the layout at 80×24 and in a 60-column split.
