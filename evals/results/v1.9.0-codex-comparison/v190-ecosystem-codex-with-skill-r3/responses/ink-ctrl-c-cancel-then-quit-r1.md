Change both the subprocess call and Ink’s Ctrl+C policy:

- **Replace `execSync` with `execFile` or `spawn`.** Synchronous work blocks the event loop, freezing spinner timers and keyboard handling. Moving `execSync` into `useEffect` won’t fix it.
- **Set `exitOnCtrlC: false`.** Ink otherwise exits before your `useInput` handler receives Ctrl+C.
- **Keep the input handler active**, including after cancellation. It keeps raw mode enabled so Ctrl+C arrives as input.

For example:

```tsx
import React, {useEffect, useRef, useState} from 'react';
import {execFile} from 'node:child_process';
import {render, Text, useAnimation, useApp, useInput} from 'ink';

function Build() {
  const {exit} = useApp();
  const controller = useRef<AbortController | null>(null);
  const [status, setStatus] = useState('Building');
  const {frame} = useAnimation({
    interval: 80,
    isActive: status === 'Building',
  });

  useEffect(() => {
    const abort = new AbortController();
    controller.current = abort;
    let mounted = true;

    execFile('your-build-command', ['--your-arg'], {
      signal: abort.signal,
    }, error => {
      if (!mounted) return;
      setStatus(
        abort.signal.aborted ? 'Cancelled' :
        error ? `Failed: ${error.message}` : 'Done',
      );
    });

    return () => {
      mounted = false;
      abort.abort();
    };
  }, []);

  useInput((input, key) => {
    if (!key.ctrl || input !== 'c') return;

    const abort = controller.current;
    if (abort && !abort.signal.aborted && status === 'Building') {
      // Signal changes synchronously: a rapid second press can quit.
      setStatus('Cancelling');
      abort.abort();
      return;
    }

    process.exitCode = 130;
    exit();
  });

  return (
    <Text>
      {status === 'Building' ? `${'|/-\\'[frame % 4]} ` : ''}
      {status} — Ctrl+C: {status === 'Building' ? 'cancel' : 'quit'}
    </Text>
  );
}

const app = render(<Build />, {exitOnCtrlC: false});
await app.waitUntilExit();
```

Use Ink’s `exit()` and await cleanup instead of calling `process.exit()`.

`AbortSignal` requests termination of the direct child; **it doesn’t guarantee termination of descendants**. If your build runs through npm or a shell and launches more processes, add process-tree cancellation appropriate to your supported platforms. For large build logs, prefer `spawn` with drained pipes over `execFile`’s buffered output, and feed logs through Ink rather than inheriting terminal output.