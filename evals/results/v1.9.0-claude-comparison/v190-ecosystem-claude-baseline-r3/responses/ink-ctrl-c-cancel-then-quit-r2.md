There's no project code in the working directory, so I can't edit your files. These are the changes to make in your code.

## Why it's broken

1. **`execSync` blocks Node's event loop.** While the build runs, Node can't run timers, re-render the UI or read keypresses. Your spinner's interval never fires, so it never moves, and Ink never sees the Ctrl+C until the build has finished.
2. **Ink quits on Ctrl+C by default.** `render()` defaults to `exitOnCtrlC: true`, so your own Ctrl+C handling never gets a chance to run.

## The fix

- Replace `execSync` with `spawn`, which runs the build without blocking.
- Keep a reference to the child process so you can kill it.
- Pass `exitOnCtrlC: false` and handle Ctrl+C yourself in `useInput`.

```tsx
import React, {useEffect, useRef, useState} from 'react';
import {render, Box, Text, useApp, useInput} from 'ink';
import Spinner from 'ink-spinner';
import {spawn, type ChildProcess} from 'node:child_process';

type Status = 'running' | 'cancelling' | 'cancelled' | 'done' | 'failed';

function killTree(proc: ChildProcess) {
	if (proc.exitCode !== null || proc.signalCode !== null || !proc.pid) return;
	try {
		// Negative pid = whole process group (npm -> sh -> tsc/webpack/etc.)
		process.kill(-proc.pid, 'SIGTERM');
	} catch {}
}

function App() {
	const {exit} = useApp();
	const [status, setStatus] = useState<Status>('running');
	const [lastLine, setLastLine] = useState('');
	const child = useRef<ChildProcess | null>(null);

	useEffect(() => {
		const proc = spawn('npm', ['run', 'build'], {
			stdio: ['ignore', 'pipe', 'pipe'], // don't let the child grab the TTY from Ink
			detached: true, // own process group so killTree reaches grandchildren
		});
		child.current = proc;

		const onData = (buf: Buffer) => {
			const line = buf.toString().trim().split('\n').pop();
			if (line) setLastLine(line);
		};
		proc.stdout!.on('data', onData);
		proc.stderr!.on('data', onData);

		proc.on('error', () => setStatus('failed'));
		proc.on('close', code => {
			child.current = null;
			setStatus(s => (s === 'cancelling' ? 'cancelled' : code === 0 ? 'done' : 'failed'));
		});

		return () => killTree(proc); // never leave an orphaned build behind
	}, []);

	useInput((input, key) => {
		if (!(key.ctrl && input === 'c')) return;

		if (status === 'running' && child.current) {
			setStatus('cancelling'); // first Ctrl+C: cancel the build
			killTree(child.current);
		} else {
			exit(); // any later Ctrl+C (or one after the build ends): quit
		}
	});

	return (
		<Box flexDirection="column">
			{status === 'running' && (
				<Text>
					<Spinner type="dots" /> Building… <Text dimColor>{lastLine}</Text>
				</Text>
			)}
			{status === 'cancelling' && <Text color="yellow">Cancelling… (Ctrl+C again to quit)</Text>}
			{status === 'cancelled' && <Text color="yellow">Build cancelled. Ctrl+C to quit.</Text>}
			{status === 'done' && <Text color="green">✔ Build finished. Ctrl+C to quit.</Text>}
			{status === 'failed' && <Text color="red">✖ Build failed. Ctrl+C to quit.</Text>}
		</Box>
	);
}

render(<App />, {exitOnCtrlC: false});
```

## Details that matter

- **`detached: true` plus `process.kill(-pid)`:** `npm run build` starts more processes underneath it. Killing only the npm process can leave the real compiler still running, so this kills the whole group.
- **Don't use `stdio: 'inherit'`:** the build would compete with Ink for the terminal and could take your keypresses.
- **The cleanup function in `useEffect`:** if you quit with the second Ctrl+C while the build is still shutting down, unmounting kills it anyway, so nothing is left running.
- **If your "build" is JavaScript running in your own process** (not a separate command), `spawn` doesn't apply. Run it in a `worker_threads` Worker and call `worker.terminate()` to cancel. Anything heavy and synchronous on the main thread will freeze the spinner in the same way.
- **`useInput` only works when stdin is a real terminal.** If you also run the CLI in CI or with piped input, add a `process.on('SIGINT', …)` handler that uses the same logic.

Share your actual component and I can apply these changes to it directly.
