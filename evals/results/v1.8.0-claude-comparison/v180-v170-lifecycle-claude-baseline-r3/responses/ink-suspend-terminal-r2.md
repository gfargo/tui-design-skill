Short answer: **yes, unmount and render again is the right basic approach. Drive it from a loop outside React, not from inside a component callback.** While Ink is mounted it owns stdin (raw mode plus a read listener) and redraws stdout. An editor needs both, so Ink has to let go of the terminal completely first.

One caveat: there's no project or `node_modules/ink` in this directory, so I couldn't check Ink 7's source. The points below rely on Ink behaviour that has been stable for several major versions (`render`, `unmount`, `waitUntilExit`, `useApp().exit`, `useStdin().isRawModeSupported`). Check the Ink 7 changelog to see whether it added a built-in way to suspend the app.

## Recommended shape

```tsx
import React from 'react';
import {render, useApp, useInput} from 'ink';
import {spawnSync} from 'node:child_process';

type Next = {kind: 'edit'; file: string} | {kind: 'quit'};

function App({state, onDone}: {state: State; onDone: (n: Next) => void}) {
  const {exit} = useApp();
  useInput((input) => {
    if (input === 'e') { onDone({kind: 'edit', file: state.file}); exit(); }
    if (input === 'q') { onDone({kind: 'quit'}); exit(); }
  });
  return /* ... */;
}

async function main() {
  let state = initialState;
  for (;;) {
    let next: Next = {kind: 'quit'};
    const app = render(<App state={state} onDone={(n) => (next = n)} />);
    await app.waitUntilExit();          // Ink has fully released the terminal

    if (next.kind === 'quit') break;

    const result = openEditor(next.file); // never throws, see below
    state = {...state, lastEdit: result};  // feed the outcome into the next render
  }
}

function openEditor(file: string): EditResult {
  if (!process.stdin.isTTY || !process.stdout.isTTY) {
    return {ok: false, reason: 'no-tty'};
  }
  const editor = process.env.VISUAL || process.env.EDITOR || 'vi';
  // Same approach as git: let sh split "$EDITOR" (e.g. "code --wait"), pass the file safely as $1
  const r = spawnSync('sh', ['-c', `${editor} "$1"`, 'sh', file], {stdio: 'inherit'});
  if (r.error) return {ok: false, reason: 'spawn-failed', error: r.error};
  if (r.signal) return {ok: false, reason: 'killed', signal: r.signal};
  if (r.status !== 0) return {ok: false, reason: 'nonzero', status: r.status};
  return {ok: true};
}
```

React state is lost when you unmount. Keep anything that must survive the editor outside React (here in `state`) and pass it back in on each render.

## Callback failure

- **Never let the editor step throw between unmount and re-render.** If it does, nothing re-renders and the process either exits silently or hangs. Return a result object, as `openEditor` does above, or wrap the step in `try/catch` and put the error into the next `state`. That way the UI comes back and shows what went wrong.
- **`spawnSync` doesn't throw if the editor can't start.** A missing binary (ENOENT) shows up as `r.error`. A non-zero exit or a signal shows up in `status` and `signal`. Check all three. If you use async `spawn`, you also need a handler for its `'error'` event.
- **Don't run the editor inside the old instance's `useInput` handler** (unmount, `spawnSync`, `render` all in one go). At that point you're still inside the dying instance's input dispatch and React commit. The outer loop avoids this.
- If a component calls `exit(error)`, `waitUntilExit()` rejects. Catch that in `main` and decide whether to re-render or exit with a non-zero code.

## Manual ownership

When you call `render()` yourself, you own the whole lifecycle:

- **Every instance must end.** Call `unmount()` or `exit()` each time before you hand over the terminal. Otherwise the old instance's stdin listener competes with the editor for keystrokes. That's especially bad with async `spawn`, where the event loop keeps running.
- **Raw mode:** Ink turns raw mode on for `useInput` and restores it on unmount. If you call `stdin.setRawMode()` yourself, Ink doesn't know about it, and you have to undo it before starting the editor.
- **Exit:** the process exit code and any final cleanup are your job after the loop ends. If you pass `exitOnCtrlC: false`, Ctrl+C becomes your job too.
- **Screen:** Ink leaves its last frame on screen. Most editors use the alternate screen, so the new render just appears below the old frame. If you want a clean slate, call `app.clear()` before exiting.

## Non-TTY behaviour

- **Don't launch an interactive editor without a TTY** (piped, CI, `| tee`). Check `process.stdin.isTTY && process.stdout.isTTY` and fall back: show an error, accept the content via stdin or a flag, or skip the edit.
- **Ink itself:** `useInput` needs raw mode and throws when stdin isn't a TTY. Check `useStdin().isRawModeSupported` and pass `useInput(handler, {isActive: isRawModeSupported})`. In CI, Ink also changes how it writes output (it skips the live redraws), so don't test the edit/re-render cycle there.

## What `waitUntilExit` is for

It returns a promise that resolves when the instance unmounts (through `exit()` or `unmount()`) and rejects if `exit(error)` was called. It's the link back to ordinary async code: "the UI is finished and the terminal is free, so do the next thing." In this pattern it's the signal that it's safe to start the editor. Without it you'd be guessing when Ink has let go of stdin and stdout.
