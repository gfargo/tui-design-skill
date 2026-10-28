You have two separate bugs:

1. **The spinner never moves because `execSync` blocks the event loop.** Ink draws frames, reads keys and runs timers on the same thread. While `execSync` runs, nothing redraws and every keypress waits in a queue until the build ends. Use the async `execFile` (or `spawn`) instead.
2. **Ctrl+C kills the app because Ink handles it before your code does.** With the default `exitOnCtrlC: true`, Ink exits on Ctrl+C and your `useInput` never sees the key. Pass `exitOnCtrlC: false` and handle Ctrl+C yourself in a `useInput` hook. That hook must stay mounted and active the whole time. If no input hook is active, Ink turns raw mode off and Ctrl+C goes back to being a plain SIGINT that kills the process.

To stop the build, give the child process an `AbortController` signal and abort it on the first Ctrl+C:

```tsx
import React, {useEffect, useRef, useState} from 'react';
import {render, Text, useAnimation, useApp, useInput} from 'ink';
import {execFile} from 'node:child_process';

type Status = 'running' | 'done' | 'cancelled' | 'failed';

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
    return () => abort.current.abort();          // never leave an orphaned build
  }, []);

  useInput((input, key) => {
    if (!key.ctrl || input !== 'c') return;
    if (status === 'running') {
      abort.current.abort();                      // first Ctrl+C: cancel the build
    } else {
      process.exitCode = status === 'done' ? 0 : status === 'failed' ? 1 : 130;
      exit();                                     // second Ctrl+C: quit through Ink's cleanup
    }
  });

  if (status === 'running') return <Text>{'|/-\\'[frame % 4]} Building… (Ctrl+C to cancel)</Text>;
  if (status === 'cancelled') return <Text>✗ Build cancelled. Press Ctrl+C again to quit.</Text>;
  if (status === 'failed') return <Text>✗ Build failed. Press Ctrl+C to quit.</Text>;
  return <Text>✓ Build done. Press Ctrl+C to quit.</Text>;
};

render(<Build cmd="npm" args={['run', 'build']} />, {exitOnCtrlC: false});
```

**Details that matter:**
- **Leave through `exit()`, not `process.exit()`.** `exit()` unmounts the app and lets Ink restore the terminal: raw mode, cursor and the last frame. If you have code after `render()`, `await waitUntilExit()` before running it.
- **Exit with 130 on cancel.** That's the usual code for "interrupted", so a chained command like `mycli && deploy` stops.
- **The build gets SIGTERM, not SIGINT.** In raw mode the terminal doesn't send SIGINT to the child, so the abort is what ends the build. `abort()` sends SIGTERM by default; use the `killSignal` option if your build tool needs something else. `npm run` passes signals on to its script, but tools that start their own child processes may need you to kill the whole process group.
- **Raise `maxBuffer` or switch to `spawn`.** `execFile` stores all output in memory and kills the child once it passes 1 MB, the default limit. A noisy build will look like a failure. If you want to show the build's output, use `spawn` with piped stdio and render the lines yourself. Don't use `stdio: 'inherit'`, because the child would write over Ink's frame.
- **The labels are part of the fix.** Saying on screen what the next Ctrl+C does keeps "first press cancels" from feeling like nothing happened. Each state has a symbol and a word, so it still reads correctly without color.
- **Prefer `<Spinner>` if you use `@inkjs/ui`.** The `useAnimation` frame counter above avoids adding a dependency. Either one only animates once the event loop is free.

**To test it,** use `ink-testing-library`: render `<Build>` with a slow command like `sleep 5` and send `\x03` (the Ctrl+C byte) to its stdin. Check that the frame changes to "cancelled", then send a second `\x03` and check that the app exited.
