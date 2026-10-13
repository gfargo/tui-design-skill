You shouldn't unmount and re-render. In Ink 7.1+ (and 8), `unmount()` is a permanent shutdown and throws away React state. Use `useApp().suspendTerminal()` instead: it lends the terminal to a child process and takes it back afterwards. This needs Ink **7.1 or later**. `suspendTerminal` doesn't exist in 7.0 or Ink 6, so check your installed version first.

## The callback form (use this by default)

```tsx
import {spawn} from 'node:child_process';
import {readFile, writeFile} from 'node:fs/promises';
import {useApp} from 'ink';

function runEditor(file: string) {
  const editor = process.env.VISUAL || process.env.EDITOR || 'vi';
  return new Promise<void>((resolve, reject) => {
    const child = spawn(editor, [file], {stdio: 'inherit', shell: true});
    child.on('error', reject);
    child.on('exit', code =>
      code === 0 ? resolve() : reject(new Error(`${editor} exited ${code}`)));
  });
}

const NoteEditor = ({file}: {file: string}) => {
  const {suspendTerminal} = useApp();
  const [text, setText] = useState('');
  const [error, setError] = useState<string>();

  const edit = async () => {
    try {
      await suspendTerminal(() => runEditor(file));
      setText(await readFile(file, 'utf8')); // reload: redraw doesn't refresh data
    } catch (e) {
      setError((e as Error).message);       // terminal is already restored here
    }
  };
  // ...
};
```

Ink pauses input and rendering, restores the cursor, input and screen modes, and runs your callback. Afterwards it re-enters and does a full redraw in a `finally` path. React state survives. The redraw only repaints that existing state, though, so you have to re-read anything the editor changed yourself.

## If the callback fails

Because re-entry happens in `finally`, a callback that throws or rejects still gets the terminal back. The error then comes out of `await suspendTerminal(...)`, so catch it there and show it in the UI. Don't let it go unhandled. A non-zero exit from the editor isn't an exception unless you make it one, as `runEditor` does above. Decide whether "user quit without saving" counts as an error or just means "no change."

## Manual ownership

When the handoff doesn't fit inside one callback, Ink gives you a suspension handle instead. You then own the resume, so it has to happen on every path:

```ts
const suspension = /* manual suspendTerminal form, see Ink readme */;
try {
  await runEditor(file);
} finally {
  await suspension.resume();
}
// or: await using suspension = ...;  (disposes → resumes at scope exit)
```

If you forget `resume()` on an error path, the app stays frozen with input paused. Check the exact call that returns the handle in the [Ink `suspendTerminal` docs](https://github.com/vadimdemedes/ink/blob/v8.0.0/readme.md#suspendterminalcallback). My reference describes the handle's `resume()` and `await using`, but not that call's signature.

Starting a second suspension while one is active is an error. Put editor and shell handoffs in one place, such as a single hook or command handler at the app root, rather than letting any component suspend.

## Non-TTY behavior

Ink still runs your callback when there's no interactive TTY, so `suspendTerminal` itself won't fail in CI or with piped stdio. Launching vim in that situation is still pointless or will hang. Check `process.stdin.isTTY && process.stdout.isTTY` before offering the action. If either is missing, hide the "edit" key, or fall back to reading input from a file, a flag, or stdin.

## What `waitUntilExit` is for

It's for the **final** shutdown at the top level, not for handoffs:

```ts
const app = render(<App />);
try {
  await app.waitUntilExit();   // resolves on exit(), rejects on exit(new Error(...))
  // safe to print summaries / set exit code here — terminal writes have flushed
} catch (err) {
  process.exitCode = 1;
}
```

Use it so post-run output and process termination wait until Ink has finished restoring the terminal. If you register SIGTERM handlers, have them call `unmount()`, then await `waitUntilExit()`, then set the exit status, and never call `process.exit()` before that. It plays no part in the editor round-trip, because the app never exits during a suspension.

**Quick test:** do one real PTY smoke run (open the editor → save → check the content reloaded and the screen redrew), plus a failing-editor case (e.g. `EDITOR=false`) to confirm the terminal comes back and the error shows. Unit-test the reload logic without a terminal.
