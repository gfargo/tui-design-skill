No—don’t unmount and call `render()` again just to launch an editor. In Ink 7.1+, keep the app mounted and use `useApp().suspendTerminal()`. It hands the terminal to `$EDITOR`, then restores Ink’s terminal modes and performs a full redraw. [Ink documentation](https://www.npmjs.com/package/ink)

```tsx
import {useApp, useStdin, useStdout} from 'ink';

function EditAction() {
	const {suspendTerminal} = useApp();
	const {stdin} = useStdin();
	const {stdout} = useStdout();

	const edit = async () => {
		if (!stdin.isTTY || !stdout.isTTY) {
			throw new Error('Editing requires an interactive terminal.');
		}

		await suspendTerminal(async () => {
			await runEditor(); // e.g. await spawnEditor(process.env.EDITOR)
		});

		// Ink is mounted and has redrawn here.
	};

	// invoke `void edit()` from input/click handler; catch and surface errors as UI state
	return null;
}
```

The callback form is the usual choice. If `runEditor()` throws or rejects, Ink still restores the terminal in `finally`, then the original failure propagates—catch it in your component and render an error state. Ink also avoids letting a redraw failure mask that editor error. [Implementation](https://raw.githubusercontent.com/vadimdemedes/ink/v7.1.1/src/ink.tsx)

For manual ownership—useful when the editor lifecycle spans more than one function—get a suspension and always resume it:

```ts
const suspension = await suspendTerminal();
try {
	await runEditor();
} finally {
	await suspension.resume();
}
```

Or use `await using` if your TypeScript/runtime setup supports async disposables. Do not nest suspensions: attempting one while another is active throws. While suspended, Ink stops handling input and emitting frames; updates made then are reflected by the forced redraw on resume. [Ink documentation](https://www.npmjs.com/package/ink)

For non-TTY/CI/piped output, Ink is non-interactive. `suspendTerminal(callback)` still runs the callback, but performs no terminal handoff—so launching a full-screen editor there is generally wrong; detect it and fail clearly or use a noninteractive fallback. Ink normally decides this from CI status and `stdout.isTTY`. [Ink source](https://raw.githubusercontent.com/vadimdemedes/ink/v7.1.1/src/ink.tsx)

`waitUntilExit()` is unrelated to suspending. It is for code outside the tree that needs to await the **whole Ink app** being unmounted: it resolves with `exit(value)`, rejects for `exit(error)`, and waits for manual-unmount stdout writes. Use the `await suspendTerminal(...)` promise to wait for the editor; use `waitUntilRenderFlush()` only when you need to wait for a frame to reach stdout. [Ink documentation](https://www.npmjs.com/package/ink)
