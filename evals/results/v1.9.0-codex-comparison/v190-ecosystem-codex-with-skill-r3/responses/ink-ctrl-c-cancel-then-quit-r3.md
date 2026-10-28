Change both the subprocess call and Ink’s Ctrl+C policy:

- **Replace `execSync` with `execFile` or `spawn`.** Synchronous work blocks the event loop, so spinner ticks and keyboard handlers cannot run. Moving `execSync` into `useEffect` still blocks.
- **Set `exitOnCtrlC: false`.** Ink otherwise exits before your `useInput` handler receives Ctrl+C.
- **Keep the input handler active**, including after cancellation. Use a ref to record cancellation immediately so a fast second press quits.

```tsx
import React, {useEffect, useRef, useState} from 'react';
import {execFile} from 'node:child_process';
import {render, Text, useAnimation, useApp, useInput} from 'ink';

function Build() {
  const {exit} = useApp();
  const controller = useRef<AbortController | null>(null);
  const cancelRequested = useRef(false);
  const running = useRef(true);
  const [status, setStatus] = useState('running');
  const {frame} = useAnimation({
    interval: 80,
    isActive: status === 'running',
  });

  useEffect(() => {
    const abort = new AbortController();
    controller.current = abort;
    let disposed = false;

    // Replace with your build executable and arguments.
    execFile(
      process.execPath,
      ['scripts/build.mjs'],
      {signal: abort.signal},
      error => {
        if (disposed) return;
        running.current = false;

        if (abort.signal.aborted) {
          setStatus('Cancelled. Ctrl+C to quit.');
        } else if (error) {
          process.exitCode = 1;
          setStatus(`Build failed: ${error.message}`);
        } else {
          setStatus('Build complete. Ctrl+C to quit.');
        }
      },
    );

    return () => {
      disposed = true;
      abort.abort();
      controller.current = null;
    };
  }, []);

  useInput((input, key) => {
    if (!key.ctrl || input !== 'c') return;

    if (running.current && !cancelRequested.current) {
      cancelRequested.current = true;
      setStatus('Cancelling… Ctrl+C again to quit.');
      controller.current?.abort();
      return;
    }

    process.exitCode = 130;
    exit();
  }); // Keep active while cancelling and after completion.

  return (
    <Text>
      {status === 'running'
        ? `${'|/-\\'[frame % 4]} Building… Ctrl+C to cancel.`
        : status}
    </Text>
  );
}

const app = render(<Build />, {exitOnCtrlC: false});
await app.waitUntilExit();
```

Use Ink’s `exit()` and await `waitUntilExit()` so terminal cleanup and pending writes finish; avoid calling `process.exit()` inside the handler.

`execFile` buffers output. Use `spawn` with piped output for large build logs, and route those logs through Ink. Also, aborting a child does **not** guarantee termination of its descendants: if you launch through npm or a shell, add process-tree cancellation appropriate to your platform.

Verify that the spinner advances during the build, the first Ctrl+C cancels, and an immediate second Ctrl+C exits cleanly with status 130.