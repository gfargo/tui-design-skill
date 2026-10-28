Change three things:

- Replace `execSync` with asynchronous `spawn`. `execSync` blocks Node’s event loop, freezing both the spinner and input handling.
- Pass `exitOnCtrlC: false` to Ink’s `render`.
- Handle Ctrl+C in `useInput`, keeping the cancellation flag in a ref so a fast second press works.

```tsx
import {spawn, type ChildProcess} from 'node:child_process';
import {useEffect, useRef, useState} from 'react';
import {render, Text, useApp, useInput} from 'ink';
import Spinner from 'ink-spinner';

function App() {
  const {exit} = useApp();
  const child = useRef<ChildProcess | null>(null);
  const cancelled = useRef(false);
  const [status, setStatus] = useState('Building');

  useEffect(() => {
    // Run your build entry point directly.
    const process = spawn(
      globalThis.process.execPath,
      ['scripts/build.js'],
      {stdio: ['ignore', 'pipe', 'pipe']},
    );

    child.current = process;

    // Drain output so a full pipe cannot stall the build.
    // You can also collect it and display it through Ink.
    process.stdout?.resume();
    process.stderr?.resume();

    process.once('error', error => {
      child.current = null;
      if (!cancelled.current) setStatus(`Failed: ${error.message}`);
    });

    process.once('close', (code, signal) => {
      child.current = null;
      if (!cancelled.current) {
        setStatus(code === 0 ? 'Done' : `Failed: ${signal ?? code}`);
      }
    });

    return () => {
      process.kill('SIGTERM');
    };
  }, []);

  useInput((input, key) => {
    if (!key.ctrl || input !== 'c') return;

    if (!cancelled.current && child.current) {
      cancelled.current = true;
      setStatus('Cancelled — press Ctrl+C to quit');
      child.current.kill('SIGTERM');
      return;
    }

    exit();
  });

  return (
    <Text>
      {status === 'Building' && <Spinner />} {status}
    </Text>
  );
}

render(<App />, {exitOnCtrlC: false});
```

In Ink’s raw input mode, Ctrl+C is handled as keyboard input; a `process.on('SIGINT')` listener alone won’t implement this interaction.

`child.kill()` signals only the direct child. If your build launches workers or runs through `npm` or a shell, use process-tree cancellation as well. Also, sending `SIGTERM` requests termination; keep tracking the child until `close`, and add a force-kill timeout if it can ignore that signal.