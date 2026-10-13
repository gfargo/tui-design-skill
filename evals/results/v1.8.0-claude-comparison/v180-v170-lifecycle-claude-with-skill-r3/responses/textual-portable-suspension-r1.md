**No. Don't exit the app, run `os.system`, and then relaunch it.** Exiting is for final shutdown. Opening an editor is a temporary handoff, and Textual 8 has separate APIs for that and for Ctrl+Z. The exit-then-relaunch approach has several problems:

- **State is lost.** Focus, scroll position, selection, undo history and in-flight workers all disappear, so the "relaunch" is really a cold start.
- **It doesn't work on Textual Web.** There's no local terminal to give to the editor. Exiting just ends the browser session, and the editor either fails or opens on the server where nobody can see it.
- **It's fragile on Windows.** `os.system` goes through `cmd.exe` and its quoting rules. Paths with spaces or `&` will break, and a shell string is an injection risk.
- **It breaks the exit code.** The parent process sees the relaunched app's exit status, or the editor's, instead of the result of the user's session. If the relaunch runs inside the old process, the stack grows with every edit.

## The lifecycle

| Boundary | API | Windows | Textual Web |
|---|---|---|---|
| Edit a file | `with self.suspend(): subprocess.run(argv)`, then reload the data | Works | Raises `SuspendNotSupported`, so offer an in-app fallback |
| Ctrl+Z | Bind it to `suspend_process`. Textual sends SIGTSTP and restores application mode on `fg` | Does nothing (Windows has no job control) | Does nothing |
| Resume after `fg` | Subscribe to `app_resume_signal` and reload data that may have changed outside the app | n/a | n/a |
| Final exit | `self.exit(result, return_code=N)`, then `sys.exit(app.return_code)` after `run()` | Same | Same |

`suspend()` lends the terminal to code inside a `with` block. `suspend_process` does Unix job control. Neither one replaces a final exit, and neither one rereads your data. Textual repaints the model you already have, so reloading anything the editor or a shell session might have changed is your job.

```python
import os, shlex, subprocess, sys
from pathlib import Path
from textual.app import App, SuspendNotSupported
from textual.binding import Binding

EXIT_OK, EXIT_ERROR, EXIT_USAGE = 0, 1, 2

def editor_argv(path: Path) -> list[str]:
    cmd = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if not cmd:
        cmd = "notepad" if sys.platform == "win32" else "vi"
    # $EDITOR may carry flags ("code --wait"); never pass it through a shell.
    return [*shlex.split(cmd, posix=(sys.platform != "win32")), str(path)]

class MyApp(App):
    BINDINGS = [
        Binding("e", "edit", "Edit"),
        Binding("ctrl+z", "suspend_process", "Suspend", show=False),
    ]

    def on_mount(self) -> None:
        self.app_resume_signal.subscribe(self, self._on_resume)

    def action_edit(self) -> None:
        path = self.current_path()           # your model
        try:
            with self.suspend():
                result = subprocess.run(editor_argv(path))
        except SuspendNotSupported:
            # Textual Web: no local terminal to hand over.
            self.open_inline_editor(path)    # e.g. a TextArea screen
            return
        except FileNotFoundError as exc:
            self.notify(f"Editor not found: {exc.filename}", severity="error")
            return
        if result.returncode != 0:
            self.notify(f"Editor exited {result.returncode}; reloading anyway",
                        severity="warning")
        self.reload_from_disk(path)          # refresh() alone won't reread it

    def _on_resume(self) -> None:
        self.reload_from_disk(self.current_path())

if __name__ == "__main__":
    app = MyApp()
    app.run()
    sys.exit(app.return_code or 0)
```

Some notes on this code:

- **Blocking is intended here.** Running the editor synchronously inside `suspend()` is fine. The app has handed over the terminal and has nothing to draw, and Textual resumes and redraws when the block exits.
- **GUI editors need a wait flag.** Something like `code` returns immediately unless `$EDITOR` includes `--wait`. Otherwise you'll reload before the user has saved, so document this.
- **Ctrl+Z can clash with undo.** `TextArea` binds Ctrl+Z to undo, so a focused text area will take that key before the app-level suspend binding sees it. That's usually the right behaviour inside a text field. Make sure suspend is still reachable from other parts of the app, or list it in the command palette.
- **Hide Suspend where it does nothing.** On Windows and Web the key is a no-op. Don't advertise "Suspend" in the footer there; check `sys.platform` or `self.is_web` before showing the hint.
- **Use a fallback outside the editor flow too.** Wherever `SuspendNotSupported` can occur, provide the in-app alternative instead of a dead key.

## Exit-code contract

Write this in `--help` and keep it short:

| Code | Meaning |
|---|---|
| `0` | The user quit normally, including after editing files |
| `1` | Unhandled error. Textual sets `return_code` to 1 when an exception escapes; the traceback is printed after the terminal is restored |
| `2` | Usage or argument error, raised before `app.run()` |
| `130` | Interrupted by SIGINT outside the app's own key handling (128 + 2) |

Add any app-specific codes explicitly, for example `3` = "user cancelled without choosing" for a summon–choose–exit tool. Rules:

- **The editor's exit status is not the app's exit status.** Report a failed editor run with `notify` and keep the session going.
- **Expose the code only through `return_code`.** `return_code` is just metadata until you pass it to `sys.exit(app.return_code)` after `run()`. Never call `sys.exit` or `os._exit` from inside a handler, because that skips the driver cleanup.
- **Results go to stdout, which the alternate screen doesn't use.** If the app returns a result, print it after `run()` returns, not while the UI is drawing.

## What to test

1. **Unit tests:** `editor_argv` with `$VISUAL`, `$EDITOR`, flags, paths containing spaces, and the Windows `posix=False` split.
2. **App harness:** patch `subprocess.run` and assert that the data reloads and the right notifications appear. Force `suspend()` to raise `SuspendNotSupported` and assert the inline fallback opens.
3. **One PTY smoke test on Unix:** press `e`, exit the editor, and check the screen has been restored. Then press Ctrl+Z, run `fg`, and check the redraw happens and the data reloads.
