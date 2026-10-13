You can't have both on Node 20. The newest Ink, chalk and commander all require Node 22, and so does the editor-suspend API. You need to either move off Node 20 or pin older versions that don't have the API.

## Recommended: move to Node 22 or 24, then pin the current majors

Node 20 reached end-of-life on 2026-04-30, so it no longer gets security fixes. Target Node 22 (maintenance LTS until 2027-04-30) or Node 24 (LTS). Node 26 becomes LTS on 2026-10-28.

```json
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

- **Ink 8** needs Node 22 or later and React 19.3 or later. If you upgrade from an older Ink, three things break: percentage `minWidth`/`maxWidth` (numbers only now), `useStdout().stdout.columns` (use `useWindowSize()` instead), and `useInput` handlers that parsed mouse or focus reports.
- **commander 15** needs Node 22.12 or later, which sets the `engines` floor above.
- **chalk 6** needs Node 22 or later.
- **Ink can't be loaded with `require()`.** If your code is CommonJS, `require('ink')` throws `ERR_REQUIRE_ASYNC_MODULE`. Use `await import('ink')` or a bundler. chalk and commander load fine with `require()` on Node 22.12+.

**The suspend API is `useApp().suspendTerminal`.** It was added in Ink 7.1, so it isn't in Ink 7.0 or Ink 6:

```tsx
const {suspendTerminal} = useApp();

async function editInEditor(file: string) {
  await suspendTerminal(async () => {
    spawnSync(process.env.EDITOR ?? 'vi', [file], {stdio: 'inherit'});
  });
  reloadFromDisk(file); // the redraw keeps the old React state, so reload what the editor changed
}
```

While the callback runs, Ink stops reading input and rendering and gives the terminal back to the editor. When the callback finishes, Ink takes the terminal back and redraws the whole screen. Points to watch:
- Don't unmount the app to do this.
- Starting a second suspension while one is active is an error, so route all editor launches through one owner, not individual components.
- If you use the manual form instead of the callback, always `await suspension.resume()` in a `finally` block.

## If you're stuck on Node 20 for now

These are the last majors that run on Node 20:

| Package | Pin |
|---|---|
| ink | `^6` (needs React 19 or later) |
| chalk | `^5` |
| commander | `^14` (security fixes until May 2027) |

With these you lose `suspendTerminal` and have to hand the terminal to the editor yourself. One way is to keep app state outside React (for example in a zustand store), unmount Ink, run the editor, then render again. Treat that as a stopgap until you can upgrade.

**My recommendation:** upgrade to Node 22 or 24 and use Ink 8. It's the only way to get both the newest versions and `suspendTerminal`, and Node 20 is already out of support.

These version numbers and Node requirements come from the tui-design skill's TypeScript reference, which lists Ink 8.0.x as current as of October 2026. I didn't check the npm registry, so run `npm view ink version` (and the same for chalk and commander) before you pin exact patch versions.
