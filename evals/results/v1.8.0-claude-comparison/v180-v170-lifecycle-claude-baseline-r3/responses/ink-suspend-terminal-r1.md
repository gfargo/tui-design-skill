I couldn't check this against Ink 7's source because this directory has no `node_modules/ink`. What follows is based on Ink's long-standing `render()` API: `rerender`, `unmount`, `waitUntilExit`, `clear` and `cleanup`. **Check the Ink 7 changelog for a built-in way to suspend Ink or hand the terminal to another program. If it has one, use it instead.**

## Short answer

Yes, unmounting, running the editor, then rendering again is the right approach. It's only safe if one outer function controls the whole cycle. Don't call `unmount()` or `render()` from inside a component.

The editor and Ink can't both run at once. Ink keeps stdin in raw mode, listens for keypresses and redraws on state changes or terminal resizes. With `stdio: 'inherit'`, the editor would compete for keystrokes and get its screen overwritten. Unmounting turns raw mode off, removes the input listeners and restores the cursor.

## Recommended structure

```tsx
import {render} from 'ink';
import {spawnSync} from 'node:child_process';

type EditRequest = {file: string};

async function main() {
  let state = initialState;

  for (;;) {
    let request: EditRequest | undefined;

    const app = render(
      <App
        state={state}
        onRequestEdit={(r) => { request = r; }} // component then calls useApp().exit()
      />
    );

    try {
      await app.waitUntilExit();
    } catch (err) {
      // The app exited with an error: exit(err) or an uncaught render error
      process.exitCode = 1;
      return;
    }

    if (!request) return; // normal quit

    const result = runEditor(request.file);
    state = result.ok
      ? applyEdit(state, result.contents)
      : {...state, error: result.message}; // show the error in the next render instead of crashing
  }
}
```

Inside the component, call `onRequestEdit(...)` and then `exit()` from `useApp()`. The component only says it wants an edit. The outer loop does the work.

## The four things you asked about

**1. Callback failure.** Things can fail in three places:
- **Your callback throws.** It runs inside React, so the error reaches Ink. Ink shows its error screen and unmounts, and `waitUntilExit()` rejects. You have to catch that rejection or you'll get an unhandled rejection.
- **The editor fails.** Check all three fields on the `spawnSync` result:
  - `result.error`: the editor wasn't found (ENOENT) or couldn't be started.
  - `result.status !== 0`: the editor exited with an error. Some editors, like `git commit`'s, use this to mean "aborted".
  - `result.signal`: the editor was killed by a signal.
  
  Return a result object instead of throwing, and render again with the error in state. Whatever happens, the loop must either render again or exit cleanly, so the terminal is never left without an owner.
- **`$VISUAL`/`$EDITOR` includes arguments**, e.g. `code --wait`. Split it into a command and its arguments, or run it with `shell: true`. Otherwise spawning fails with ENOENT. Use `$VISUAL ?? $EDITOR ?? 'vi'`.

**2. Manual ownership.** Whatever code calls `render()` owns that instance and is the only code that should call `unmount()`, `clear()` or `render()` again. This matters because Ink keeps one instance per stdout stream. If you call `render()` on `process.stdout` while the old instance is still mounted, Ink updates the old instance instead of creating a new one. That's why the loop waits for `waitUntilExit()` before rendering again. Also:
- Keep any state that must survive the editor outside React and pass it back in as props. Unmounting erases all hook state.
- Ink's last frame stays in the scrollback. If you don't want the next render to print below it, call `app.clear()` before exiting.
- `cleanup()` only removes Ink's internal record of the instance. It's mainly for tests and isn't a way to unmount.

**3. Non-TTY behavior.** An interactive editor needs a real terminal. Check before starting it:

```ts
const interactive = process.stdin.isTTY && process.stdout.isTTY;
```

If that's false, don't start the editor. Instead, read the input from a file, a flag or piped stdin, or fail with a clear error message. Inside Ink, `useInput` needs raw mode, which isn't available without a TTY. Gate it with `useStdin().isRawModeSupported`, otherwise Ink throws "Raw mode is not supported". Ink also detects CI environments and writes only the final frame there, so a render-edit-render loop wouldn't work in CI anyway.

**4. What `waitUntilExit` is for.** It returns a promise that:
- resolves when the app unmounts, either because something called `exit()` or because the instance was unmounted, and
- rejects if the app exited with an error, via `exit(err)` or an uncaught render error.

Use it to wait until Ink has fully let go of the terminal before running anything else. That makes it the right point to start the editor. Don't use it as a channel for return values; pass results out through a callback or a variable, as `request` does above.

## One more thing: Ctrl-C while the editor is open

Once Ink is unmounted, its Ctrl-C handling is gone. Full-screen editors like vim take Ctrl-C themselves. But with an editor that doesn't, a Ctrl-C sends SIGINT to your process as well and can kill it mid-loop. If that matters, ignore SIGINT while the editor runs:

```ts
const ignore = () => {};
process.on('SIGINT', ignore);
try { /* spawnSync editor */ } finally { process.off('SIGINT', ignore); }
```
