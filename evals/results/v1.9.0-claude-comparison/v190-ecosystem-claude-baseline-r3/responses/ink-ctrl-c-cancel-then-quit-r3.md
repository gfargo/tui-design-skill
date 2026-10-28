I couldn't find any source files in the working directory, so this is based on the two symptoms you described. They have two separate causes.

## 1. `execSync` blocks the event loop (why the spinner is stuck)

While `execSync` runs, Node can't do anything else. It can't fire timers, so the spinner doesn't move. It can't read stdin, so your keys sit unread. And it can't re-render. Use async `spawn` instead.

## 2. Ink exits on Ctrl+C by default (why the app dies)

`render()` defaults to `exitOnCtrlC: true`, so Ink quits before your code sees the key. Turn that off and handle Ctrl+C yourself in `useInput`.

## The fix

```tsx
import React, {useEffect, useRef, useState} from 'react';
import {render, Text, useApp, useInput} from 'ink';
import Spinner from 'ink-spinner';
import {spawn, type ChildProcess} from 'node:child_process';

type Status = 'building' | 'cancelled' | 'done' | 'failed';

function App() {
  const {exit} = useApp();
  const [status, setStatus] = useState<Status>('building');
  const child = useRef<ChildProcess | null>(null);

  useEffect(() => {
    const proc = spawn('npm', ['run', 'build'], {
      stdio: ['ignore', 'pipe', 'pipe'], // don't let the child write over Ink or read your keys
      detached: true,                    // own process group, so the whole tree can be killed
    });
    child.current = proc;

    proc.on('exit', (code, signal) => {
      child.current = null;
      setStatus(s => (s === 'cancelled' ? s : signal || code !== 0 ? 'failed' : 'done'));
    });

    return () => killBuild(); // stop the build if the app exits
  }, []);

  const killBuild = () => {
    const proc = child.current;
    if (proc?.pid) {
      try {
        process.kill(-proc.pid, 'SIGTERM'); // negative pid = the whole process group
      } catch {}
    }
  };

  useInput((input, key) => {
    if (!(key.ctrl && input === 'c')) return;

    if (status === 'building') {
      setStatus('cancelled'); // first Ctrl+C cancels the build
      killBuild();
    } else {
      exit();                 // second Ctrl+C (or any Ctrl+C after the build ends) quits
    }
  });

  return (
    <Text>
      {status === 'building' && (
        <>
          <Text color="cyan"><Spinner type="dots" /></Text> Building… <Text dimColor>(Ctrl+C to cancel)</Text>
        </>
      )}
      {status === 'cancelled' && <Text color="yellow">Build cancelled. Press Ctrl+C again to quit.</Text>}
      {status === 'done' && <Text color="green">✔ Build finished. Ctrl+C to quit.</Text>}
      {status === 'failed' && <Text color="red">✖ Build failed. Ctrl+C to quit.</Text>}
    </Text>
  );
}

render(<App />, {exitOnCtrlC: false});
```

## Why each piece is there

- **`exitOnCtrlC: false`**: Ink stops handling Ctrl+C itself, and it arrives in `useInput` as `input === 'c'` with `key.ctrl`.
- **You have to kill the child yourself.** Ink puts the terminal in raw mode, so Ctrl+C is just a keypress. The terminal doesn't send SIGINT to anything, including the build.
- **`detached: true` plus `process.kill(-pid)`**: `npm run build` starts its own children (tsc, webpack, etc.). Killing only the `npm` process can leave those running. Killing the negative pid hits the whole group. On Windows, use `taskkill /pid <pid> /T /F` instead.
- **`stdio: ['ignore', 'pipe', ...]`**: if the child inherits stdout, its output gets mixed into Ink's rendering. If it inherits stdin, it can take your keypresses. To show build output, read `proc.stdout` and render the last few lines yourself.
- **Status check in the `exit` handler**: if the user cancels, the build exits with a signal. The check keeps that from being shown as "failed".

If you'd rather have Ctrl+C quit right away whenever no build is running, the `else` branch already does that.
