I can't give you exact verified version numbers from here. There's no `package.json` or lockfile in this directory, and I have no network access to check npm. Today is 2026-10-13, and my knowledge stops at mid-2026, so some of the "newest" releases may be newer than what I know. Run this to get the real answers:

```sh
npm view ink version engines.node peerDependencies
npm view chalk version engines.node
npm view commander version engines.node
```

Pin the newest version whose `engines.node` still includes 20.

**Node 20 reached end-of-life on 2026-04-30.** It's no longer LTS. Packages are starting to drop it, which is the real limit on "newest." Moving to Node 22 or 24 would let you take the actual latest of all three.

**What I know about each (check against the commands above):**

| Package | Line that works on Node 20 | Notes |
|---|---|---|
| ink | **6.x** | Ink 6 requires Node ≥20 and React 19, so pin `react@^19` too. If an Ink 7 exists, check its engines before using it. |
| chalk | **5.x** (≥5.6.2) | ESM-only and supports old Node versions, so Node 20 is fine. **Avoid `5.6.1`**: it was the malicious version in the September 2025 npm supply-chain attack. |
| commander | **14.x** | v14 requires Node ≥20. Commander said v15 would require a newer Node (22+) and go ESM-only, so v15 likely won't work for you. |

Use exact pins (`"ink": "6.x.y"`) plus a committed lockfile, not caret ranges. That matters more after the chalk incident.

**On the suspend API:** as of my knowledge, Ink has **no official API for suspending the UI**. There's a long-standing feature request, but nothing like `instance.suspend()` / `resume()`. Search the changelog for your pinned version in case one was added since. The reliable pattern is to unmount Ink, run the editor, then render again:

```js
import {render} from 'ink';
import {spawnSync} from 'node:child_process';

let instance = render(<App onEdit={openEditor} />);

function openEditor(file) {
  instance.unmount();                      // releases raw mode and stops Ink from writing
  const editor = process.env.VISUAL || process.env.EDITOR || 'vi';
  spawnSync(editor, [file], {stdio: 'inherit'});   // editor owns the TTY until it exits
  instance = render(<App onEdit={openEditor} />);  // fresh mount
}
```

Things that make this work:
- **Keep state outside React** (a store or module-level object). Unmounting throws away component state, so the new mount has to rebuild from that.
- **Use `spawnSync` or await the child's exit before calling `render` again.** Otherwise Ink and the editor fight over stdout and stdin.
- **Wrap the editor command for a shell** (`spawnSync(editor, [file], {stdio:'inherit', shell: true})` or split it) if `$EDITOR` can contain arguments, like `code --wait`.
- **If you use `waitUntilExit()`**, the unmount will resolve it. Don't let your app's exit logic run in that case.

If you install the packages here, I can read Ink's actual typings in `node_modules/ink` to check whether your pinned version adds a suspend-style API.
