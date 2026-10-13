I can't check the npm registry from here, and there's no `package.json` in this directory. This is based on what I knew as of mid-2026, so confirm the versions with `npm view <pkg> versions engines` before you pin.

## Versions

| Package | Pin | Notes |
|---|---|---|
| **ink** | `^6` (newest 6.x) | Ink 6 needs Node ≥ 20 and React 19, so it fits. Pin `react@^19` alongside it. If a later Ink major exists, check that its `engines` field still allows Node 20. |
| **chalk** | `5.6.2` or newer, **not `5.6.1`** | Chalk 5 is ESM-only. Version 5.6.1 was the malicious release in the September 2025 npm supply-chain attack, and it was pulled. Use an exact pin or a lockfile, and make sure `5.6.1` doesn't appear in your lockfile. |
| **commander** | `^14` | Commander 14 needs Node ≥ 20. Commander 15 was planned as ESM-only with a minimum of **Node 22.12**. If it has shipped, it's the newest version but won't support Node 20, so stay on 14. |

Pin the newest version that supports your Node version, even if a newer major exists. `npm view commander@latest engines` will tell you quickly.

## Suspending Ink while `$EDITOR` runs

As far as I know, Ink has no built-in API for suspending and resuming the UI. People have asked for one in Ink's GitHub issues, but nothing had shipped as of my knowledge. Check the changelog for your Ink version in case something was added. The usual workaround is to unmount, run the editor, and re-render:

```js
import {render} from 'ink';
import {spawnSync} from 'node:child_process';

let app = render(<App onEdit={editFile} />);

function editFile(path) {
  app.unmount();                    // also restores raw mode on stdin
  spawnSync(process.env.EDITOR || 'vi', [path], {stdio: 'inherit'});
  app = render(<App onEdit={editFile} />);  // state must live outside the tree
}
```

Some caveats:
- Any state you need after the editor closes has to live outside the component tree, for example in a store or passed in as props.
- Wait for `app.waitUntilExit()` before spawning the editor so Ink finishes cleaning up.
- If you want to keep the tree mounted instead, you can try `setRawMode(false)` from `useStdin()` around `spawnSync`. Ink will still redraw over the editor, though, so unmounting is the more reliable approach.

If you share your `package.json` or let me run `npm view`, I can confirm the exact latest versions.
