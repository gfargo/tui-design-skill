**No. `unmount()` followed by a second `render()` is the wrong approach.** In Ink 7.1+, use `useApp().suspendTerminal()`. Note that this API was added in 7.1. It isn't in 7.0, so if you're on 7.0, upgrade to 7.1 or to Ink 8, which has the same contract.

## Why unmount + render is wrong

`unmount()` is a permanent shutdown, not a pause:

- **You lose your state.** All React state is discarded and every effect cleanup runs. The second `render()` starts a new app from its initial state: selection, scroll position and form input are all gone.
- **The exit path fires.** `waitUntilExit()` resolves, so any top-level code that runs after the app exits (printing a summary, setting the exit code) runs partway through the session.
- **Input is torn down and rebuilt.** You end up re-implementing raw mode, the alternate screen and redraw yourself, and the frame flickers or tears.

`suspendTerminal` does what you actually need. It pauses Ink's input and rendering and gives the terminal back to the shell (cursor, input modes, screen buffer). It runs your callback, then switches the terminal back and does a full redraw. Your React tree stays mounted the whole time.

## Callback form (recommended)

```tsx
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {readFile} from 'node:fs/promises';
import {useCallback, useRef, useState} from 'react';
import {useApp} from 'ink';

async function runEditor(file: string): Promise<number> {
  const [cmd, ...args] = (process.env.VISUAL || process.env.EDITOR || 'vi').split(/\s+/);
  const child = spawn(cmd, [...args, file], {stdio: 'inherit'});
  const [code] = await once(child, 'exit'); // rejects on spawn 'error' (e.g. ENOENT)
  return code ?? 1;
}

export function useEditFile(file: string) {
  const {suspendTerminal} = useApp();
  const busy = useRef(false);
  const [content, setContent] = useState<string>();
  const [error, setError] = useState<string>();

  const edit = useCallback(async () => {
    if (busy.current) return;            // overlapping suspension is an error
    busy.current = true;
    try {
      const code = await suspendTerminal(() => runEditor(file));
      setError(code === 0 ? undefined : `Editor exited with ${code}`);
    } catch (err) {
      setError(`Could not run editor: ${(err as Error).message}`);
    } finally {
      busy.current = false;
      setContent(await readFile(file, 'utf8').catch(() => undefined)); // reload
    }
  }, [file, suspendTerminal]);

  return {edit, content, error};
}
```

**Callback failure.** Ink switches the terminal back and redraws in a `finally` block, so the terminal is restored even when your callback throws or rejects. Ink doesn't swallow the error, so catch it yourself and show it in the UI (as the `catch` above does). A failed launch (no editor installed, `ENOENT`) and a nonzero editor exit are different results, so report them separately.

**Reload after the editor returns.** The redraw only repaints your current React state. It doesn't know the file changed. Re-read anything the editor could have modified, including after a failure, because the editor may have written the file before it crashed.

## Manual ownership

Use this form when the suspension can't fit inside a single callback:

```ts
const suspension = await suspendTerminal();
try {
  await runEditor(file);
} finally {
  await suspension.resume();   // always, or the UI stays frozen
}

// or, if your TS target/runtime supports explicit resource management:
await using suspension = await suspendTerminal();
await runEditor(file);
```

- With manual ownership you are responsible for calling `resume()`. If you miss it on any path, the app's input and rendering stay paused for good.
- Only one suspension can be active at a time; starting a second one while one is active throws. Put all handoffs behind one hook or provider, like `useEditFile` with its `busy` guard. Don't let individual components call `suspendTerminal` directly.

## Non-TTY behavior

When there's no interactive TTY, Ink still runs your callback; it just doesn't switch any terminal modes. Ink handles this correctly, but your app still shouldn't launch an interactive editor with no terminal attached. Check `process.stdin.isTTY && process.stdout.isTTY` before offering the edit action. Without a TTY, either hide the action or fall back to a non-interactive path such as reading input from a file or an argument, and fail with a clear message. Also note that `alternateScreen: true` is ignored in CI and when stdout is piped.

## What `waitUntilExit` is for

`waitUntilExit()` is only for the final shutdown, at the top level:

```ts
const app = render(<App />, {alternateScreen: true});
try {
  await app.waitUntilExit();      // resolves after exit()/unmount and pending writes flush
  console.log('Saved.');          // post-run output goes here, not before
} catch (err) {                   // rejects if the app called exit(new Error(...))
  console.error((err as Error).message);
  process.exitCode = 1;           // set exitCode; don't call process.exit() before the flush
}
```

It has nothing to do with the editor handoff. If you await it inside the app it won't resolve until the app shuts down. If you treat it as a "pause finished" signal, you're back in the unmount + render pattern.

**Ctrl+Z:** If you also want Ctrl+Z to suspend the app (Unix only), send SIGTSTP from inside `suspendTerminal` so the resume path switches the terminal back and redraws. Windows has no job-control suspend, so provide a different action there.

**Testing:** Unit-test `useEditFile` with a fake `runEditor` that succeeds, exits nonzero and throws. In each case, check the error message, that `busy` is reset, and that the file is reloaded. Then do one PTY smoke test with a real editor (or `EDITOR=true`) to confirm the screen is fully redrawn and keys work again afterward.
