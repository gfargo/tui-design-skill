No—on **Ink 7.1+**, use `useApp().suspendTerminal()` rather than unmounting and rendering again. It preserves your React tree/state, gives the editor the terminal, then restores Ink and forces a full redraw. (`suspendTerminal` was added in 7.1.0.) [Ink release](https://github.com/vadimdemedes/ink/releases), [API docs](https://www.npmjs.com/package/ink?activeTab=versions)

```tsx
const {suspendTerminal} = useApp();

async function edit() {
  try {
    await suspendTerminal(async () => {
      await runEditor(); // spawn with stdio: 'inherit'
    });

    setStatus('Saved'); // Ink has resumed and redrawn
  } catch (error) {
    setStatus(`Editor failed: ${String(error)}`);
  }
}
```

If `runEditor()` throws or rejects, Ink still restores its terminal state and redraws; the `suspendTerminal()` promise then rejects, so catch it if the app should continue.

For manual ownership—when the editor/session must outlive a single callback—always resume in `finally`:

```ts
const suspension = await suspendTerminal();
try {
  await runEditor();
} finally {
  await suspension.resume();
}
```

`resume()` is async. Ink also supports `await using` for automatic disposal. Do not nest suspensions; attempting one while already suspended throws.

In non-TTY/CI output, Ink runs the callback but performs **no** terminal handoff. An interactive editor generally cannot work there, so explicitly reject/skip that action (usually require both `stdin.isTTY` and `stdout.isTTY`).

`waitUntilExit()` is unrelated to opening the editor. It is for code outside the app that must run after the whole Ink app unmounts; it resolves with `exit(value)`, rejects for `exit(error)`, and waits for teardown output after manual `unmount()`. Use `waitUntilRenderFlush()` if you specifically need to sequence work after a frame is written.
