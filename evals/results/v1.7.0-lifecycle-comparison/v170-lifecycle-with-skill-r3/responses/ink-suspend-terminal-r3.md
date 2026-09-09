No. For a temporary `$EDITOR` handoff, keep the Ink app mounted and use `useApp().suspendTerminal()`.

```tsx
import {useApp, useInput} from 'ink';
import {useRef, useState} from 'react';

function EditorAction() {
  const {suspendTerminal} = useApp();
  const [error, setError] = useState<string>();
  const opening = useRef(false);

  const openEditor = async () => {
    if (opening.current) return;

    if (!process.stdin.isTTY || !process.stdout.isTTY) {
      setError('Cannot open an interactive editor without a TTY.');
      return;
    }

    opening.current = true;
    setError(undefined);

    try {
      await suspendTerminal(async () => {
        const result = await runEditorWithInheritedStdio();
        if (result.exitCode !== 0) {
          throw new Error(`Editor exited with ${result.exitCode}`);
        }
      });

      await reloadFileThatEditorMayHaveChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      opening.current = false;
    }
  };

  useInput(input => {
    if (input === 'e') void openEditor();
  });

  return null;
}
```

`suspendTerminal` temporarily gives the terminal to the editor: Ink stops consuming input/output, restores normal terminal modes (including leaving the alternate screen), then restores Ink and fully redraws when the callback settles. If the callback throws or rejects, Ink still restores the terminal; the returned promise rejects, so catch it to show an error. Reload any editor-mutated data afterward—a redraw does not refresh your React state. [Ink v7.1.1 docs](https://github.com/vadimdemedes/ink/blob/v7.1.1/readme.md#suspendterminalcallback)

If you need manual ownership, always resume in `finally` (or use `await using`):

```ts
const suspension = await suspendTerminal();
try {
  await runEditorWithInheritedStdio();
} finally {
  await suspension.resume();
}
```

Do not let arbitrary components create suspensions: a second overlapping suspension throws. [Ink docs](https://github.com/vadimdemedes/ink/blob/v7.1.1/readme.md#suspendterminalcallback)

For non-TTY output, Ink still invokes the callback but performs no terminal handoff. That does *not* make an interactive editor viable; explicitly reject it or provide a noninteractive alternative such as `--file`, stdin input, or a plain error message.

`unmount()` is final shutdown: it destroys the React tree. Rendering again would require reconstructing state, subscriptions, and terminal ownership, and is the wrong lifecycle for “open editor, then continue.”

`waitUntilExit()` belongs at the render boundary after a permanent exit/unmount. It resolves with `exit(value)`, rejects with `exit(error)`, and for manual `unmount()` waits until unmount-related stdout writes finish. It is not an editor-resume primitive. [Ink lifecycle docs](https://github.com/vadimdemedes/ink/blob/v7.1.1/readme.md#render)
