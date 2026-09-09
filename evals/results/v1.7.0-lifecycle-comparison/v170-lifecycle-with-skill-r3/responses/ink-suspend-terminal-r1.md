No—don’t unmount and call `render()` again for a temporary editor handoff. In Ink 7, keep the React tree mounted and use `useApp().suspendTerminal()`:

```tsx
import {useApp, useInput} from 'ink';

function EditConfig() {
	const {suspendTerminal} = useApp();

	useInput((input) => {
		if (input !== 'e') return;

		void (async () => {
			try {
				await suspendTerminal(async () => {
					await runEditor(); // e.g. spawn $EDITOR with stdio: 'inherit'
				});

				// Ink is rendering again here. Reload any file the editor changed.
				await reloadConfig();
			} catch (error) {
				// Terminal state has already been restored.
				showError(error instanceof Error ? error.message : String(error));
			}
		})();
	});

	return /* normal Ink UI */;
}
```

`suspendTerminal` temporarily stops Ink input/rendering and restores the terminal state the editor needs: raw mode off, cursor visible, alt-screen exited, etc. When the callback settles—successfully or by throwing—Ink restores its own state and fully redraws. A redraw does not reload your data, so explicitly reload editor-mutated files afterward.

If the callback fails, terminal restoration still happens, then `await suspendTerminal(...)` rejects. Catch it to put the UI into an error state; don’t rely on `finally` alone to hide the failure.

Use manual ownership only when the suspension must span code that cannot fit cleanly in one callback:

```ts
const suspension = await suspendTerminal();

try {
	await runEditor();
} finally {
	await suspension.resume(); // mandatory, and async
}
```

Or, with TypeScript’s disposable support:

```ts
await using suspension = await suspendTerminal();
await runEditor();
```

Never allow arbitrary components to independently suspend: a second overlapping suspension throws. Centralize this terminal ownership.

For non-TTY/CI output, the callback still runs, but Ink performs no terminal handoff. An interactive editor generally cannot work there, so guard it and offer a clear fallback or fail with a useful message:

```ts
if (!process.stdin.isTTY || !process.stdout.isTTY) {
	throw new Error('Editing requires an interactive terminal.');
}
```

`waitUntilExit()` is for the *permanent* application boundary, not for returning from the editor. It resolves after the app unmounts (and manual-unmount output writes finish), or rejects if `exit(new Error(...))` was used:

```ts
const {waitUntilExit} = render(<App />, {alternateScreen: true});
const result = await waitUntilExit();
// Safe place for post-app output / process-level cleanup.
```

Use `unmount()`/`exit()` plus `waitUntilExit()` when the Ink session is truly over. Re-rendering after unmounting discards component state and is only appropriate for a new app instance—not an editor round trip. Ink also documents that reusing the same stdout across multiple `render()` calls without unmounting is unsupported. [Ink 7.1.1 lifecycle docs](https://github.com/vadimdemedes/ink/blob/v7.1.1/readme.md#suspendterminalcallback)
