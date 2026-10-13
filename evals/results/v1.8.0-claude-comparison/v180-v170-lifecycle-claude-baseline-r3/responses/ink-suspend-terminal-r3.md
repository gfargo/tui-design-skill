Yes, unmounting and rendering again is the right basic approach, with one change: don't run the editor from inside the component. Run it from the code that called `render()`. The component only says "I want to edit X" and exits. That outer code waits for the unmount, runs the editor, then renders again.

I couldn't check Ink 7's source or changelog because there's no project or `node_modules` in this directory. What follows uses only `render`, `unmount`, `waitUntilExit` and `useApp().exit`, which Ink has had for a long time. Check the Ink 7 release notes for a built-in "suspend" helper; if there is one, use it instead.

## Why you have to unmount

While it's mounted, Ink controls the terminal. It puts stdin in raw mode, hides the cursor, redraws stdout and listens for keypresses. Vim, nano or `code --wait` need the terminal to themselves. If Ink stays mounted, it redraws over the editor and both read the same keystrokes. Unmounting gives the terminal back: raw mode is restored, the cursor is shown again and the listeners are removed.

## Pattern

```tsx
import React from 'react';
import {render, useApp, useInput} from 'ink';
import {spawnSync} from 'node:child_process';

type Next = {kind: 'edit'; file: string} | {kind: 'quit'};
type EditResult = {ok: true} | {ok: false; reason: string};

function App({lastEdit, onNext}: {lastEdit?: EditResult; onNext: (n: Next) => void}) {
  const {exit} = useApp();
  useInput((input) => {
    if (input === 'e') { onNext({kind: 'edit', file: 'notes.md'}); exit(); }
    if (input === 'q') { onNext({kind: 'quit'}); exit(); }
  });
  // ...render lastEdit status, etc.
  return null;
}

function runEditor(file: string): EditResult {
  if (!process.stdin.isTTY || !process.stdout.isTTY) {
    return {ok: false, reason: 'not a TTY; cannot open an interactive editor'};
  }
  const editor = process.env.VISUAL || process.env.EDITOR || 'vi';
  // shell: true so EDITOR="code --wait" works; quote the path yourself
  const r = spawnSync(`${editor} ${JSON.stringify(file)}`, {stdio: 'inherit', shell: true});
  if (r.error) return {ok: false, reason: r.error.message};          // e.g. ENOENT
  if (r.signal) return {ok: false, reason: `editor killed by ${r.signal}`};
  if (r.status !== 0) return {ok: false, reason: `editor exited ${r.status}`};
  return {ok: true};
}

async function main() {
  let lastEdit: EditResult | undefined;
  for (;;) {
    let next: Next = {kind: 'quit'};
    const app = render(<App lastEdit={lastEdit} onNext={(n) => { next = n; }} />);
    try {
      await app.waitUntilExit();
    } finally {
      app.cleanup?.(); // optional: drops the instance so the next render() is a fresh one
    }
    if (next.kind === 'quit') break;
    lastEdit = runEditor(next.file); // Ink is fully unmounted here
  }
}

main().catch((err) => { console.error(err); process.exitCode = 1; });
```

## Callback failure

There are two places this can fail:

- **The editor fails.** `$EDITOR` might not exist (`r.error`), it might exit non-zero (`:cq` in vim), or it might be killed by a signal. None of these should crash your app. Turn the failure into a value (`EditResult`) and pass it into the next render so the UI can say "editor exited 1" and let the user try again. Decide on purpose what non-zero means. For git-style tools it means "abort", so don't use the file.
- **Your own code fails.** This includes an `onNext` callback that throws, or post-edit processing that throws, such as parsing the edited file. React error boundaries only catch errors thrown during rendering. They don't catch errors from event handlers, `useInput` callbacks or code that runs after `waitUntilExit`. So:
  - Inside the component, wrap risky callback code in `try/catch` and either put the error in state or call `exit(err)`. `exit(err)` makes `waitUntilExit()` reject, which sends the error to the outer loop.
  - In the outer loop, wrap post-edit processing too. Otherwise a parse error escapes the loop and the process ends without rendering again. Catch it, put it in `lastEdit`, and keep looping.
  - Keep `try/finally` around the Ink part so a rejected `waitUntilExit` still cleans up.

## Manual ownership

When you drive `render()` yourself like this, you own the lifecycle, and Ink won't clean up for you:

- **You decide when the app ends.** Return values come back through your closure (`next`), not through Ink. Don't rely on `exit()` passing a value through `waitUntilExit()`; behaviour has varied between versions.
- **Anything you set on the terminal, you undo.** If you call `process.stdin.setRawMode`, add your own `SIGINT`/`SIGTERM` handlers, enter the alternate screen or hide the cursor yourself, reverse it before launching the editor and set it up again after. Ink only undoes what Ink did.
- **Ctrl+C.** With the default `exitOnCtrlC: true`, Ink unmounts on Ctrl+C and `waitUntilExit` resolves. `next` stays at its default `'quit'`, so the loop ends correctly. If you set `exitOnCtrlC: false`, handle Ctrl+C in `useInput`. While the editor is running, the editor gets Ctrl+C, because `stdio: 'inherit'` gives it the terminal.
- **Use `spawnSync`, not async `spawn`.** With async `spawn`, Node's event loop keeps running. Anything still reading `process.stdin` (a leftover listener, a timer that calls `render`) can steal keystrokes or draw over the editor. `spawnSync` blocks everything until the editor closes. If you need async, make sure nothing renders or reads stdin until the child's `close` event.
- **Leftover output.** Ink's last frame stays on screen above the editor session. If you want a clean screen, clear it before launching the editor.

## Non-TTY behavior

If stdin or stdout isn't a TTY (piped input, `> file`, CI), there's no terminal to give the editor:

- Terminal editors will complain ("Output is not to a terminal") or hang waiting for input.
- Ink's `useInput` needs raw mode. On a non-TTY stdin it can't use it and will error (see `useStdin().isRawModeSupported`). Ink also usually writes only the final frame in CI.

So check `process.stdin.isTTY && process.stdout.isTTY` before offering the edit action at all, not just inside `runEditor`. In non-TTY mode, use a different path: read the content from a flag, a file or piped stdin, or fail with a clear message ("--edit requires an interactive terminal").

## What `waitUntilExit` is for

It returns a promise that **resolves when the Ink instance unmounts**, whether through `exit()`, `unmount()` or Ctrl+C. It **rejects if you call `exit(error)`**. Its job is ordering: it's how the outer code knows Ink has given the terminal back and the editor can start. It's also how errors from inside the tree get out.

It does not keep the process alive, return your app's result or restore anything you changed on the terminal yourself. Calling `unmount()` from outside and then starting the editor immediately also works, because unmount is synchronous. But going through `exit()` and `await waitUntilExit()` keeps the decision inside the component and the error handling in one place.
