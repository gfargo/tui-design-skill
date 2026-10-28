I couldn't find your code in the working directory, so this is based on what you described. There are two problems, and each needs its own fix.

## Why it breaks

1. **`execSync` blocks the event loop.** While the build runs, Node can't run timers, re-render, or read stdin. The spinner's `setInterval` never fires, and `useInput` never sees your keypresses.
2. **Ink handles Ctrl+C itself.** Ink puts the terminal in raw mode, so Ctrl+C doesn't send a SIGINT signal. It arrives as the byte `\x03`, and by default (`exitOnCtrlC: true`) Ink exits when it sees it. Your keypress waits in the input buffer until `execSync` returns, and then Ink quits the app.

## The fix

- Replace `execSync` with async `spawn` so the event loop stays free.
- Render with `exitOnCtrlC: false` and handle Ctrl+C yourself in `useInput`.

```tsx
import React, {useEffect, useRef, useState} from 'react';
import {render, Text, useApp, useInput} from 'ink';
import Spinner from 'ink-spinner';
import {spawn, type ChildProcess} from 'node:child_process';

type Status = 'running' | 'cancelled' | 'done' | 'failed';

function Build() {
  const {exit} = useApp();
  const [status, setStatus] = useState<Status>('running');
  const child = useRef<ChildProcess | null>(null);

  useEffect(() => {
    // detached: child gets its own process group, so we can kill
    // the whole tree (npm -> tsc/webpack/etc.), not just the shell.
    const proc = spawn('npm', ['run', 'build'], {detached: true, stdio: 'ignore'});
    child.current = proc;

    proc.on('exit', (code, signal) => {
      child.current = null;
      setStatus(s => (s === 'cancelled' ? s : signal ? 'cancelled' : code === 0 ? 'done' : 'failed'));
    });

    return () => killTree(proc); // don't orphan the build on unmount
  }, []);

  useInput((input, key) => {
    if (!(key.ctrl && input === 'c')) return;

    if (status === 'running' && child.current) {
      setStatus('cancelled');
      killTree(child.current);   // first Ctrl+C: cancel the build
    } else {
      exit();                    // second Ctrl+C (or build finished): quit
    }
  });

  if (status === 'running') {
    return <Text><Spinner type="dots" /> Building… <Text dimColor>(Ctrl+C to cancel)</Text></Text>;
  }
  if (status === 'cancelled') {
    return <Text color="yellow">Build cancelled. Press Ctrl+C again to quit.</Text>;
  }
  return <Text color={status === 'done' ? 'green' : 'red'}>Build {status}. Press Ctrl+C to quit.</Text>;
}

function killTree(proc: ChildProcess) {
  if (proc.pid == null || proc.exitCode !== null) return;
  try {
    process.kill(-proc.pid, 'SIGTERM'); // negative pid = whole process group
  } catch {
    proc.kill('SIGTERM');
  }
}

render(<Build />, {exitOnCtrlC: false});
```

## Details that matter

- **`exitOnCtrlC: false` is required.** Without it, Ink exits on the first Ctrl+C before your handler runs.
- **`detached: true` plus `process.kill(-pid)`.** `npm run build` starts a shell, which starts the real tool. `child.kill()` only kills the top process, and the actual build keeps running. Killing the process group stops all of them. This works on macOS and Linux. On Windows, use `taskkill /pid <pid> /T /F` or the `tree-kill` package.
- **`stdio: 'ignore'`.** Don't use `'inherit'`, because the build's output would write over Ink's render. If you want to show build output, use `'pipe'`, collect `proc.stdout` lines into state, and render the last few.
- **Set `'cancelled'` before killing.** The `exit` handler checks for that status, so a cancel doesn't show up as "failed" just because the build exited with a non-zero code.
- **Optional:** add a timeout after `SIGTERM` that sends `SIGKILL` if the build ignores the first signal.

If you paste your component, I can apply these changes directly to your code.
