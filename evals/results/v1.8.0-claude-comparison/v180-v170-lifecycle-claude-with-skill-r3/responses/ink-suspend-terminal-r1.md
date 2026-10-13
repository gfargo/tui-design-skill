**No.** Unmount and `render()` again is the wrong approach. `unmount()` is final shutdown: it destroys the React tree and all its state, and it resolves `waitUntilExit()`, which the top level treats as "the app is done." To hand the terminal to an editor and then take it back, use `suspendTerminal` from `useApp()`. Check your exact version first: it was added in **Ink 7.1** and doesn't exist in 7.0. If you're on 7.0, upgrade rather than building a workaround with unmount and remount.

## Recommended shape

```tsx
import {spawn} from 'node:child_process';
import {useApp, useInput} from 'ink';

function runEditor(file: string): Promise<number> {
  const editor = process.env.VISUAL || process.env.EDITOR || 'vi';
  return new Promise((resolve, reject) => {
    const child = spawn(editor, [file], {stdio: 'inherit', shell: true});
    child.on('error', reject);
    child.on('exit', code => resolve(code ?? 1));
  });
}

const EditAction = ({file, onReload}: {file: string; onReload: () => Promise<void>}) => {
  const {suspendTerminal} = useApp();

  useInput(async input => {
    if (input !== 'e') return;
    try {
      const code = await suspendTerminal(() => runEditor(file));
      if (code !== 0) {/* show a status-line message: "editor exited with 1" */}
    } catch (err) {
      /* show the error in the UI; the terminal is already restored */
    }
    await onReload(); // redraw repaints old state, so reload the file yourself
  });

  return null;
};
```

`suspendTerminal` pauses Ink's input and rendering and restores the cursor and the input and screen modes. It then runs your callback and, in `finally`, puts the terminal back and does a full redraw. The redraw only repaints your current React state. It does not re-read the file, so call your own reload after the editor exits.

## Callback failure

The terminal comes back in `finally`, so the same thing happens whether the callback resolves, rejects, or throws (for example, `spawn` failing with ENOENT because `$EDITOR` points to a missing binary). Ink re-enters raw mode and the alternate screen, redraws, and passes the rejection on to your `await`. In practice:

- Catch the error after `suspendTerminal` and show it in the UI. Don't `console.error` it, because the TUI owns the screen again by then.
- Treat a non-zero editor exit code as a result, not an exception. `git commit` treats an aborted edit this way.
- Don't call `exit()` or `process.exit()` inside the callback. That mixes the temporary handoff with final shutdown.

## Manual ownership

There is also a manual form for when the handoff can't fit in one callback, such as when it spans several steps. Here, resuming is your job:

```ts
const suspension = await suspendTerminal();   // manual form
try {
  await runEditor(file);
} finally {
  await suspension.resume();
}
// or: await using suspension = await suspendTerminal();
```

If you skip `resume()` on any path, the app stays paused with the terminal in shell mode. Use the callback form unless you really need the manual one. Also, a second suspension that overlaps the first throws an error. Put editor launching in one place (a single hook or controller) instead of letting any component suspend whenever it wants.

## Non-TTY behavior

Without an interactive TTY, `suspendTerminal` still runs your callback and has no terminal modes to restore. That doesn't mean the editor will work. With stdin piped or in CI, `vi` will hang or fail. Check before you offer the action:

```ts
const {isRawModeSupported} = useStdin();
const canEdit = process.stdin.isTTY && process.stdout.isTTY && !process.env.CI;
```

If `canEdit` is false, hide or disable the `e` binding and print the file path, or fail with a clear message. More generally, if stdout isn't a TTY, the whole app should drop to plain output rather than running an interactive Ink UI.

## What `waitUntilExit` is for

It belongs at the top level, outside the component tree, and it marks **final** shutdown:

```ts
const app = render(<App />);
try {
  const result = await app.waitUntilExit(); // resolves on exit(value) / unmount()
  // safe to print post-run output here; Ink's writes have flushed
} catch (err) {
  // exit(new Error(...)) rejects it
  process.exitCode = 1;
}
```

Use it to know when the app has finished, to flush Ink's pending writes before printing anything else, and to set the exit status. If you handle SIGTERM, do it at this boundary: `unmount()`, `await waitUntilExit()`, set `exitCode`, then remove the listeners. Keep it out of the editor flow. If you unmount to launch the editor, `waitUntilExit()` resolves partway through the session, and your top level will think the app has quit.

## Test checklist

- Run a unit test where the editor runner is a stub that resolves, rejects, and returns a non-zero code. Check that the reload runs and the error appears in the UI.
- Run one PTY smoke test that launches a real editor with `EDITOR=true` and with a missing binary. Confirm that raw mode, cursor, and the alternate screen are restored and the frame redraws.
- Run it with stdin piped to confirm the edit action is disabled.

On Unix, if you also want Ctrl+Z, do the SIGTSTP inside `suspendTerminal` so the same code path handles resume. On Windows, offer a different action.

These details come from the skill's Ink reference, not from running anything here. Before relying on the manual form's exact signature and on the overlap and non-TTY behavior, check them against the [`suspendTerminal` docs](https://github.com/vadimdemedes/ink/blob/v8.0.0/readme.md#suspendterminalcallback) for your Ink version.
