No—on Ink **7.1+**, don’t unmount and call `render()` again just to run `$EDITOR`. Keep the existing React tree and use `useApp().suspendTerminal()`. It hands the TTY to the editor, then restores Ink’s modes and fully redraws your current UI. This is exactly the editor/pager/fzf use case. [Ink 7.1 release](https://github.com/vadimdemedes/ink/releases), [Ink API](https://github.com/vadimdemedes/ink)

```tsx
const {suspendTerminal} = useApp();

const edit = async () => {
  try {
    await suspendTerminal(async () => {
      await runEditor(tempFile); // spawn with stdio: 'inherit'
    });

    setValue(await readFile(tempFile, 'utf8'));
    setStatus('Updated from editor');
  } catch (error) {
    setStatus(`Editor failed: ${messageFrom(error)}`);
  }
};
```

Invoke it non-blockingly from `useInput` (`void edit()`), and disable the key while an editor is already open. A nested suspension throws.

Callback form is the normal choice: Ink restores the terminal even if `runEditor()` throws or rejects, then rethrows so your `catch` can decide whether to show an error, retain old content, or exit. Treat a non-zero editor exit as a product decision—usually retain the old value and show a concise status.

Use manual ownership only when the suspended interval must span work outside one callback:

```ts
const suspension = await suspendTerminal();
try {
  await runEditor(tempFile);
} finally {
  await suspension.resume(); // await this redraw/terminal restoration
}
```

`await using suspension = await suspendTerminal()` is also supported where your TypeScript target supports async disposables.

For non-TTY/CI output, don’t launch an interactive editor by default. Require a value/file option, emit a clear error, or use plain output. Ink’s suspension callback still runs in non-interactive mode, but there is no terminal handoff; Ink itself only writes its final frame on unmount in that mode. Check both `stdin.isTTY` and `stdout.isTTY` before offering the editor action. [Ink non-interactive behavior](https://github.com/vadimdemedes/ink/blob/master/src/ink.tsx)

`waitUntilExit()` is unrelated to the editor lifecycle. It is for the **outer CLI entry point** to await final app teardown:

```ts
const app = render(<App />);
try {
  await app.waitUntilExit(); // resolves after exit/unmount
  // post-UI cleanup or process result handling
} catch (error) {
  // exit(error) reaches here
}
```

It is not needed before or after `suspendTerminal()`. Unmount + fresh `render()` is only appropriate for actually ending/replacing the Ink instance—e.g. changing renderer configuration—not for temporarily yielding terminal ownership.
