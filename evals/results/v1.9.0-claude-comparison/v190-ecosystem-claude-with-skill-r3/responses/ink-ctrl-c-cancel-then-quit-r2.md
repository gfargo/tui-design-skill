Two things are wrong, and each fixes one symptom.

1. **`execSync` blocks the event loop.** Ink draws frames, runs timers and reads keys on that one loop. While `execSync` runs, nothing redraws, so the spinner freezes, and keypresses wait in a queue until the build finishes. Run the build with the async `execFile` or `spawn` instead, and pass an `AbortSignal` so you can cancel it.
2. **Ink quits on Ctrl+C before your code sees it.** `exitOnCtrlC` is on by default, so Ink exits before your `useInput` handler runs. Pass `exitOnCtrlC: false` and handle `key.ctrl && input === 'c'` yourself. Keep that `useInput` hook active the whole time. If no input hook is active, Ink turns raw mode off and Ctrl+C goes back to being a plain SIGINT that kills the process.

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
    execFile(cmd, args, {signal: abort.current.signal, maxBuffer: 64 * 1024 * 1024}, error => {
      if (!error) setStatus('done');
      else setStatus(error.name === 'AbortError' ? 'cancelled' : 'failed');
    });
    return () => abort.current.abort();  // never leave the build orphaned on unmount
  }, []);

  useInput((input, key) => {
    if (!key.ctrl || input !== 'c') return;
    if (status === 'running') {
      abort.current.abort();             // first Ctrl+C: cancel the build
    } else {
      process.exitCode = 130;            // second Ctrl+C: quit
      exit();
    }
  });

  if (status === 'running') return <Text>{'|/-\\'[frame % 4]} {cmd} {args.join(' ')}  (Ctrl+C to cancel)</Text>;
  if (status === 'cancelled') return <Text>✗ Build cancelled. Press Ctrl+C again to quit.</Text>;
  if (status === 'failed') return <Text>✗ Build failed. Press Ctrl+C to quit.</Text>;
  return <Text>✓ Build finished. Press Ctrl+C to quit.</Text>;
};

const app = render(<Build cmd="npm" args={['run', 'build']} />, {exitOnCtrlC: false});
await app.waitUntilExit();
```

What changed and why:

- **`execSync` → `execFile` with `signal`:** The loop stays free, so `useAnimation` can redraw the spinner. Calling `abort()` stops the child process (Node sends it SIGTERM) and calls back with an `AbortError`. You can then show "cancelled" instead of "failed".
- **`maxBuffer`:** `execFile` holds all of the build's output in memory, and the 1 MB default is easy for a chatty build to pass. If you don't need that output, use `spawn(cmd, args, {signal, stdio: 'ignore'})` and listen for `close` instead.
- **The status line says what the next Ctrl+C does.** That way the second press isn't a surprise. You could also quit right away when the build finished cleanly, since no work is lost.
- **Exit code 130** after a cancel+quit lets something like `mycli && deploy` stop. Call `exit()` from `useApp()` (don't use `process.exit()`) and await `waitUntilExit()` so Ink restores the terminal before the process ends.
- **The cleanup in `useEffect`** cancels the build on any other exit path.

One limit: with `exitOnCtrlC: false`, you only get Ctrl+C as a key while stdin is in raw mode. A SIGTERM (for example from a process manager) doesn't go through this path. If that matters, register one SIGTERM handler where you call `render`: abort the build, unmount, then await `waitUntilExit()`.

**Testing:** Use `ink-testing-library`. Mock `execFile`, write `'\x03'` to `stdin` and check for the "cancelled" frame, then write it again and check that the app exited. You don't need a real terminal for that.
