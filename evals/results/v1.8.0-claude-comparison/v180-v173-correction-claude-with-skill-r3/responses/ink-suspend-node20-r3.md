You can't get all of that on Node 20. The newest Ink (8.0.x), chalk 6 and commander 15 all require Node ≥ 22. Ink's suspend API, `useApp().suspendTerminal`, was added in Ink 7.1, which also requires Node 22. Ink 6 is the last major that runs on Node 20, and it has no suspend API.

Node 20 also reached end-of-life on 2026-04-30. I'd move the runtime rather than downgrade the libraries.

## Recommended: move to Node 22 or 24, then pin the newest majors

```jsonc
{
  "engines": { "node": ">=22.12" },
  "dependencies": {
    "ink": "^8.0.0",
    "react": "^19.3.0",
    "chalk": "^6.0.0",
    "commander": "^15.0.0"
  }
}
```

- **Which Node:** Node 24 is the active LTS. Node 22 is in maintenance until 2027-04-30. Node 26 becomes LTS on 2026-10-28, so Node 24 is the safer target for now.
- **Why `>=22.12`:** commander 15 needs Node 22.12 or later, which is stricter than Ink's plain `>=22`.
- **React:** Ink 8 needs React 19.3 or later (Ink 7 needed 19.2).
- **ESM:** Ink can't be loaded with `require()` because of a top-level await in its layout engine (Yoga). From CommonJS, use `await import('ink')` or a bundler. chalk and commander can still be `require()`d on Node 22.12+.

These ranges come from the skill's notes as of October 2026. Run `npm view ink version` and the same for the other packages before you lock exact patch versions.

## Handing off to `$EDITOR` with `suspendTerminal`

```tsx
import {spawnSync} from 'node:child_process';
import {useApp} from 'ink';

function useEditFile(reload: () => Promise<void>) {
  const {suspendTerminal} = useApp();
  return async (file: string) => {
    await suspendTerminal(async () => {
      spawnSync(process.env.VISUAL ?? process.env.EDITOR ?? 'vi', [file], {stdio: 'inherit'});
    });
    await reload(); // the redraw keeps the old React state, so re-read what the editor changed
  };
}
```

- **What Ink does for you:** it pauses input and rendering and gives the terminal back to the shell. When the editor exits, it re-enters and does a full redraw.
- **Reload afterwards:** the redraw repaints your existing state. It doesn't re-read the file, so call your reload step yourself.
- **Don't unmount:** `exit()` and `unmount()` end the app for good. Use them only for final shutdown, never to make room for the editor.
- **One suspension at a time:** starting a second overlapping suspension throws an error. Put the editor handoff in a single hook or service instead of letting any component call it.
- **Ctrl+Z:** Ink has no built-in job-control action. If you want Unix suspend, send SIGTSTP inside `suspendTerminal`, and offer a different action on Windows.

## If you truly can't leave Node 20 yet

Use **ink@^6, react@^19, chalk@^5, commander@^14** as a short-term bridge. commander 14 gets security fixes until May 2027.

You'd lose `suspendTerminal`, so you'd have to write the editor handoff yourself. That means:
1. Pause Ink's input.
2. Turn off raw mode and leave the alternate screen.
3. Run the editor with `stdio: 'inherit'`.
4. Restore all of that afterwards on every exit path, then force a redraw.

That's the kind of hand-written terminal cleanup that leaves people's shells broken. It's one more reason to upgrade Node rather than build it.
