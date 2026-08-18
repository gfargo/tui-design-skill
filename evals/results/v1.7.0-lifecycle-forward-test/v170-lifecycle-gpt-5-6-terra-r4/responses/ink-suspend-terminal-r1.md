No. For an editor you intend to return from, use Ink 7’s `suspendTerminal`; `unmount()` is for final shutdown, not a temporary handoff.

```tsx
import {useApp} from 'ink';

function EditConfig() {
  const {suspendTerminal} = useApp();

  const edit = async () => {
    try {
      await suspendTerminal(async () => {
        await runEditor(); // e.g. child process with stdio: 'inherit'
      });

      await reloadConfig(); // the editor may have changed external state
    } catch (error) {
      // Terminal is already restored and Ink has redrawn here.
      showEditorError(error);
    }
  };

  // call edit from useInput / a button handler
}
```

`suspendTerminal` pauses Ink output and input, restores the terminal modes an editor expects (including leaving the alternate screen), runs the callback, then re-enters Ink and forces a redraw. If the callback rejects or throws, Ink still restores the terminal; the `await suspendTerminal(...)` then rejects, so catch it at the component/application boundary. If a failed editor can still partially write the file, reload in a `finally`-style path before showing the error.

For manual ownership, resume exactly once:

```ts
const suspension = await suspendTerminal();
try {
  await runEditor();
} finally {
  await suspension.resume();
}
```

`resume()` is async because Ink may need to order terminal writes and repaint. `await using suspension = await suspendTerminal()` is also supported. Do not let arbitrary components do this independently: a second overlapping suspension throws.

In non-TTY/CI output, the callback still runs, but Ink performs no terminal handoff. An interactive editor generally cannot work there, so explicitly choose a fallback—such as a `--config-file`/noninteractive mode—or report a clear error.

`waitUntilExit()` belongs at the `render()` boundary:

```ts
const app = render(<App />, {alternateScreen: true});
await app.waitUntilExit();
// safe: final output / cleanup after Ink has unmounted and flushed
```

It waits for permanent app exit/unmount (and resolves/rejects with `exit(value/error)`); after a manual `unmount()`, it also waits for unmount-related stdout writes. It is not how to wait for an editor or resume rendering. [Ink 7 lifecycle and suspension docs](https://github.com/vadimdemedes/ink/blob/v7.1.1/readme.md#suspendterminalcallback)
