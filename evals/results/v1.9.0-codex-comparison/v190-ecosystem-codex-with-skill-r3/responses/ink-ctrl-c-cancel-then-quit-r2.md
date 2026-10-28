Change both the subprocess call and Ink’s input policy:

- **Replace `execSync` with `execFile` or `spawn`.** Synchronous work blocks the event loop, freezing animation and keyboard handling. Wrapping `execSync` in a promise won’t fix it.
- **Set `exitOnCtrlC: false`.** Ink otherwise exits before your `useInput` handler handles Ctrl+C.
- **Keep the Ctrl+C handler active after cancellation**, and use `exit()` so Ink restores the terminal.

For a directly launched build process:

```tsx
import React, {useEffect, useRef, useState} from 'react';
import {execFile} from 'node:child_process';
import {render, Text, useAnimation, useApp, useInput} from 'ink';

function Build() {
  const {exit} = useApp();
  const controller = useRef<AbortController | null>(null);
  const cancelRequested = useRef(false);
  const [status, setStatus] = useState('running');
  const {frame} = useAnimation({
    interval: 80,
    isActive: status === 'running',
  });

  useEffect(() => {
    const abort = new AbortController();
    controller.current = abort;
    let mounted = true;

    execFile(
      process.execPath,
      ['scripts/build.mjs'], // Replace with your build executable/args.
      {signal: abort.signal},
      error => {
        if (!mounted) return;
        setStatus(
          abort.signal.aborted ? 'cancelled' : error ? 'failed' : 'done',
        );
      },
    );

    return () => {
      mounted = false;
      abort.abort();
      controller.current = null;
    };
  }, []);

  useInput((input, key) => {
    if (!key.ctrl || input !== 'c') return;

    if (status === 'running' && !cancelRequested.current) {
      // Record this immediately: a second press can precede a rerender.
      cancelRequested.current = true;
      setStatus('cancelling');
      controller.current?.abort();
      return;
    }

    process.exitCode = 130;
    exit();
  }); // Always active, including while cancelling or cancelled.

  return (
    <Text>
      {status === 'running'
        ? `${'|/-\\'[frame % 4]} Building — Ctrl+C cancels`
        : `${status} — Ctrl+C quits`}
    </Text>
  );
}

const app = render(<Build />, {exitOnCtrlC: false});
await app.waitUntilExit();
```

An active `useInput` keeps Ink’s raw input handling enabled; disabling it after cancellation can make Ctrl+C become a terminal SIGINT again.

`AbortSignal` targets the launched child. If your command launches descendants through npm or a shell, use process-tree cancellation appropriate to your platform. Also capture or pipe build logs into your UI rather than inheriting stdout over the spinner.

Verify that the spinner advances during the build, the first Ctrl+C leaves the UI showing cancellation, and a rapid second press exits cleanly.