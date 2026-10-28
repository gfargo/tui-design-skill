`execSync()` blocks Node’s event loop, so Ink can’t animate the spinner or handle input. Ink also exits on Ctrl+C by default.

Use an asynchronous child process, disable Ink’s default Ctrl+C behavior, and track whether cancellation has been requested:

```jsx
import React, {useEffect, useRef, useState} from 'react';
import {spawn} from 'node:child_process';
import {render, Text, useApp, useInput} from 'ink';
import Spinner from 'ink-spinner';

function App() {
  const {exit} = useApp();
  const child = useRef(null);
  const cancelled = useRef(false);
  const [status, setStatus] = useState('building');

  useEffect(() => {
    const proc = spawn('your-build-command', [], {
      // Keep terminal input owned by Ink.
      stdio: ['ignore', 'ignore', 'pipe'],
    });

    child.current = proc;

    // Drain stderr; optionally collect it for an error summary.
    proc.stderr.resume();

    proc.once('error', error => {
      setStatus(`Failed: ${error.message}`);
    });

    proc.once('close', code => {
      child.current = null;
      setStatus(
        cancelled.current
          ? 'Cancelled. Press Ctrl+C to quit.'
          : code === 0
            ? 'Build complete.'
            : `Build failed (${code}).`,
      );
    });

    return () => {
      proc.kill('SIGTERM');
    };
  }, []);

  useInput((input, key) => {
    if (!key.ctrl || input !== 'c') return;

    if (cancelled.current || !child.current) {
      child.current?.kill('SIGKILL');
      exit();
      return;
    }

    cancelled.current = true;
    setStatus('Cancelling…');
    child.current.kill('SIGINT');
  });

  return (
    <Text>
      {status === 'building' ? <Spinner /> : null} {status}
    </Text>
  );
}

render(<App />, {exitOnCtrlC: false});
```

Replace `your-build-command` with the executable and pass its arguments as the second argument to `spawn`.

**If the command launches subprocesses**—as `npm run build` often does—`child.kill()` only signals the immediate child. On macOS/Linux, spawn with `detached: true` and signal the process group with `process.kill(-child.pid, signal)` for cancellation and cleanup. Windows requires a process-tree termination strategy.

Also keep other synchronous work out of the render path: disabling `exitOnCtrlC` alone won’t unblock the spinner.