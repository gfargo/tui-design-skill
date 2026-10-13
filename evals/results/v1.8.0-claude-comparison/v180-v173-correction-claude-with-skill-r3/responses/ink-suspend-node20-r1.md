You can't get all three on Node 20. Newest Ink, Ink's editor-suspend API, and newest chalk and commander all require Node 22. On Node 20 you also lose the suspend API itself.

**Why:**
- **The suspend API** is `useApp().suspendTerminal()`. It was added in Ink 7.1 and isn't in Ink 7.0 or Ink 6.
- **Newest versions:** Ink 8 (8.0.x, Oct 2026) needs Node 22 or later and React 19.3 or later. chalk 6 needs Node 22 or later. commander 15 needs Node 22.12 or later.
- **Node 20** reached end-of-life on 2026-04-30. The last versions that support it are Ink 6, chalk 5 and commander 14. Ink 6 has no `suspendTerminal`.

## Recommended: move to Node 22 or 24
Node 22 is in maintenance LTS until 2027-04-30. Node 24 is the current LTS. Pin:

```json
"engines": { "node": ">=22.12" },
"dependencies": {
  "ink": "^8.0.0",
  "react": "^19.3.0",
  "chalk": "^6.0.0",
  "commander": "^15.0.0"
}
```

The `>=22.12` floor comes from commander 15. Ink 8 and chalk 6 alone would only need 22.

Opening `$EDITOR` from inside a component:

```tsx
import {spawnSync} from 'node:child_process';
import {useApp} from 'ink';

const {suspendTerminal} = useApp();

async function editFile(path: string) {
  await suspendTerminal(async () => {
    spawnSync(process.env.EDITOR ?? 'vi', [path], {stdio: 'inherit'});
  });
  await reloadFromDisk(path); // the redraw keeps old React state, so re-read what the editor changed
}
```

How it behaves:
- **During the call,** Ink pauses input and rendering and gives the terminal back to the editor.
- **When the editor exits,** Ink re-enters its terminal modes and redraws the whole screen.
- **Don't unmount** the app to launch the editor.
- **Only one suspension can run at a time.** A second overlapping call throws an error. Put the call in one place, such as a single "open in editor" action, rather than letting any component call it.

## Only if you're stuck on Node 20 for now
`ink@^6`, `react@^19`, `chalk@^5`, `commander@^14`. commander 14 gets security fixes until May 2027. Treat this as temporary, because there's no `suspendTerminal`. You'd have to hand the terminal over and restore it yourself, and that's exactly the error-prone part the API exists to handle.

Two more notes:
- Ink can't be `require()`d from CommonJS, even on Node 22, so use `await import('ink')` or a bundler. chalk and commander do load through `require(esm)`.
- These version numbers come from the skill's reference, so they're as current as that reference is. I didn't query npm. Run `npm view ink version` (and the same for chalk and commander) to confirm the latest patch releases before you lock them in.
