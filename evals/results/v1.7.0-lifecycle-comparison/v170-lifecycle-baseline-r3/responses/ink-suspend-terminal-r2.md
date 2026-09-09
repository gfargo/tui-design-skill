No—don’t unmount and render a new Ink app just to run `$EDITOR`. In Ink **7.1+**, use `useApp().suspendTerminal()`: it gives the editor ownership of the terminal, then restores Ink and fully redraws the existing component tree. It was added in Ink 7.1.0. [Release notes](https://github.com/vadimdemedes/ink/releases/tag/v7.1.0)

```tsx
import {useCallback, useState} from 'react';
import {Text, useApp, useInput} from 'ink';

function App({file, canUseEditor}: {file: string; canUseEditor: boolean}) {
	const {suspendTerminal} = useApp();
	const [status, setStatus] = useState('Press e to edit');

	const openEditor = useCallback(async () => {
		if (!canUseEditor) {
			setStatus('Editor unavailable: stdin/stdout are not interactive terminals.');
			return;
		}

		setStatus('Opening editor…');

		try {
			await suspendTerminal(async () => {
				await runEditor(file); // spawn with {stdio: 'inherit'}
			});

			setStatus('Editor closed; Ink has resumed.');
		} catch (error) {
			setStatus(`Editor failed: ${error instanceof Error ? error.message : String(error)}`);
		}
	}, [canUseEditor, file, suspendTerminal]);

	useInput(input => {
		if (input === 'e') void openEditor();
	});

	return <Text>{status}</Text>;
}
```

With the callback form, Ink suspends output/input handling, restores normal terminal modes for the child (including leaving raw mode and showing the cursor), and guarantees its restoration/redraw in a `finally` path—even if `runEditor()` throws or rejects. The editor error still propagates from `await suspendTerminal(...)`, so handle it at the call site as above. [Ink 7.1.1 implementation](https://raw.githubusercontent.com/vadimdemedes/ink/v7.1.1/src/ink.tsx), [API docs](https://raw.githubusercontent.com/vadimdemedes/ink/v7.1.1/readme.md)

If you need to own the handoff manually, always resume in `finally`:

```ts
const suspension = await suspendTerminal();

try {
	await runEditor(file);
} finally {
	await suspension.resume();
}
```

This is useful when the handoff spans more than one operation. Don’t nest suspensions; Ink rejects a second suspension until the first is resumed. `resume()` is async because Ink must restore terminal state and complete the redraw. [API docs](https://raw.githubusercontent.com/vadimdemedes/ink/v7.1.1/readme.md)

For non-TTY/CI or piped output, don’t launch an inherited interactive editor. Ink normally treats those as non-interactive and writes only its final dynamic frame on unmount. `suspendTerminal(callback)` still calls the callback there, but performs no terminal handoff—so make editor availability an explicit app policy, e.g. pass the same `interactive` decision you use for `render()` as `canUseEditor`. [Ink options](https://raw.githubusercontent.com/vadimdemedes/ink/v7.1.1/src/ink.tsx)

`waitUntilExit()` is unrelated to the editor handoff. It is the outer-program lifecycle promise: it settles when the Ink app unmounts, resolves with `exit(value)`, rejects with `exit(error)`, and—after a manual `unmount()`—waits for teardown writes to stdout. Use it around your top-level `render()` if you need post-exit work; don’t use it to wait for a redraw after editing. For that, `suspendTerminal()` already waits for the restore/redraw; `waitUntilRenderFlush()` is for explicitly waiting on an ordinary Ink render. [Lifecycle docs](https://raw.githubusercontent.com/vadimdemedes/ink/v7.1.1/readme.md)

If you are on **7.0.x**, this API does not exist; upgrading is preferable. The unmount/re-render workaround ends the React tree and loses its state, so reserve it for actually terminating one Ink session and starting a separate one.
