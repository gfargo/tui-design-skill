You need two changes. They fix two separate problems.

## 1. The spinner is frozen because `execSync` blocks the event loop

Ink renders frames, runs the spinner's timer and reads keystrokes all on Node's single event loop. `execSync` holds that loop until the build finishes. So no frames render, and your Ctrl+C keypress waits in a queue until it's too late to matter. Switch to the async `execFile` (or `spawn`) and pass it an `AbortSignal` so you can cancel the build.

## 2. Ctrl+C kills the app because Ink handles it first

By default (`exitOnCtrlC: true`), Ink exits on Ctrl+C before your `useInput` handler ever sees the key. Pass `exitOnCtrlC: false` to `render` and handle Ctrl+C yourself in a `useInput` hook. Keep that hook always active (no `isActive: false`). When no input hook is active, Ink turns raw mode off, and then Ctrl+C becomes a plain SIGINT that kills the process again.

## Putting it together

```tsx
import React, {useEffect, useRef, useState} from 'react';
import {render, Text, useAnimation, useApp, useInput} from 'ink';
import {execFile} from 'node:child_process';

type Status = 'running' | 'cancelled' | 'failed' | 'done';

const Build = ({cmd, args}: {cmd: string; args: string[]}) => {
  const {exit} = useApp();
  const [status, setStatus] = useState<Status>('running');
  const abort = useRef(new AbortController());
  const {frame} = useAnimation({interval: 80, isActive: status === 'running'});

  useEffect(() => {
    // Async: the event loop stays free, so the spinner animates and keys arrive
    execFile(cmd, args, {signal: abort.current.signal}, error => {
      if (!error) setStatus('done');
      else setStatus(error.name === 'AbortError' ? 'cancelled' : 'failed');
    });
  }, []);

  useInput((input, key) => {
    if (!key.ctrl || input !== 'c') return;
    if (status === 'running') {
      abort.current.abort();          // first Ctrl+C: cancel the build
    } else {
      process.exitCode = status === 'done' ? 0 : 130;
      exit();                         // second Ctrl+C: quit through Ink's cleanup
    }
  });

  if (status === 'running') return <Text>{'|/-\\'[frame % 4]} Building… (Ctrl+C to cancel)</Text>;
  if (status === 'cancelled') return <Text color="yellow">✗ Build cancelled. Press Ctrl+C again to quit.</Text>;
  if (status === 'failed') return <Text color="red">✗ Build failed. Press Ctrl+C to quit.</Text>;
  return <Text color="green">✓ Build done. Press Ctrl+C to quit.</Text>;
};

const app = render(<Build cmd="npm" args={['run', 'build']} />, {exitOnCtrlC: false});
await app.waitUntilExit();
```

If you'd rather use a ready-made spinner, `<Spinner>` from `@inkjs/ui` works too. Don't use `ora` inside Ink, because it writes to the terminal on its own and fights Ink's rendering.

## Details worth getting right

- **Quit with `exit()`, not `process.exit()`.** `exit()` lets Ink restore the terminal (raw mode, cursor) before the process ends. Await `waitUntilExit()` before printing any final summary.
- **Exit code:** use 130 when the user interrupted, so a chained command like `cli && deploy` stops.
- **The status line has to say what the next Ctrl+C does.** "Press Ctrl+C again to quit" tells users the first press worked. Without it they press repeatedly and can't tell what happened. Each state above also uses a different symbol and wording, not just a different color, so it still reads correctly under `NO_COLOR`.
- **Aborting only kills `npm` itself.** The signal goes to the `npm` process, and its child build tools (tsc, webpack, etc.) can keep running. If you see leftover processes, run the build with `spawn(..., {detached: true})` and kill the whole process group with `process.kill(-child.pid, 'SIGTERM')`. On Windows, run `npm` with `shell: true` (or call `npm.cmd`), and use `taskkill /T` to kill the process tree, since process groups don't exist there.
- **SIGTERM is a separate case.** `exitOnCtrlC` only covers Ctrl+C typed into the app. If something like CI or a supervisor sends SIGTERM, handle it once at the top level: unmount, await `waitUntilExit()`, then set the exit code.
- **Not a TTY:** if `process.stdin.isTTY` is false (for example in CI), raw mode isn't available. Skip the spinner and keypress handling there, print plain progress lines, and let SIGINT behave normally.
