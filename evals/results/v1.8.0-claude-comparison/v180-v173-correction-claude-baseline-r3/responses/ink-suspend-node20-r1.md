I can't give you verified "newest" version numbers. I have no npm or web access in this session, this directory has no `package.json`, and today's date is past my knowledge cutoff. Run `npm view <pkg> version engines` to check the current releases. Here's what I'm confident about and what you should check.

## Node 20 has reached end of life

Node 20 LTS reached end of life on **April 30, 2026**. Packages are starting to drop it, so "newest" and "Node 20" may no longer be compatible. Moving to Node 22 or 24 LTS fixes most of the problems below.

## Per package

| Package | Last line I know supports Node 20 | Notes |
|---|---|---|
| **ink** | `^6` (needs Node ≥20 and **React 19**) | Check `npm view ink engines`. A newer major may require Node 22. |
| **chalk** | `^5.6.2` | ESM-only. **Avoid `5.6.1`**: it was the malicious release in the September 2025 npm supply-chain compromise. Pin exactly and commit your lockfile. |
| **commander** | `^14` (needs Node ≥20) | Commander announced that v15 would be ESM-only and require **Node ≥22.12**. If v15 is out, "newest" won't run on Node 20, so stay on 14. |

To check them all at once:
```sh
npm view ink version engines peerDependencies
npm view chalk version engines
npm view commander version engines
```

## Suspending Ink while $EDITOR runs

As far as I know, Ink has **no dedicated suspend/resume API**. If a newer release has added one, it will be in the changelog. Until then, the usual approach is to unmount, give the terminal to the editor, then render again:

```js
import {render} from 'ink';
import {spawnSync} from 'node:child_process';

let app = render(<App onEdit={editFile} />);

function editFile(path) {
  app.unmount();                       // restores the terminal and releases raw mode
  spawnSync(process.env.EDITOR || 'vi', [path], {stdio: 'inherit'});
  app = render(<App onEdit={editFile} />);  // keep state outside the component tree
}
```

If you need to keep the React tree mounted, you can instead call `setRawMode(false)` from `useStdin()`, run `spawnSync` with `stdio: 'inherit'`, then call `setRawMode(true)`. This is less reliable: Ink keeps drawing and its output can mix with the editor's screen. Unmounting and rendering again is the safer default.

My recommendation: if you have to stay on Node 20, pin `ink@^6`, `react@^19`, `chalk@5.6.2` and `commander@^14`, after checking the `engines` fields above. If you can upgrade Node, move to 22 or 24 first and then take the latest of everything.
