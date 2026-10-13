**No, don't call `os.system` after `self.exit()` and relaunch.** `exit()` ends the app for good. Handing the terminal to an editor is a temporary loan, and Textual 8 has an API for that: `App.suspend()`. Exiting and relaunching causes several problems:

- **It throws away state.** You lose focus, scroll position, selection, undo history and in-flight workers, so the relaunch can't put the user back where they were.
- **It runs a shell.** `os.system` passes `$EDITOR` and the file path through `sh`/`cmd.exe`, which brings quoting bugs and injection risk. It also handles `.cmd` shims and spaces in paths differently on each platform.
- **It hides the real exit code.** The process can no longer report a single, meaningful exit code. Scripts can't tell "user quit" from "editor failed" from "relaunch crashed".
- **It doesn't work on Textual Web.** The editor would start on the server, attached to no terminal the user can see.

## Lifecycle

| Event | API | Unix | Windows | Textual Web |
|---|---|---|---|---|
| **Edit** | `with self.suspend(): subprocess.run(argv)` | Editor gets the terminal; app resumes and redraws | Same | Raises `SuspendNotSupported` → open an in-app `TextArea` editor screen instead |
| **Ctrl+Z** | Bind to the built-in `suspend_process` action | Stops the process (SIGTSTP); `fg` resumes it and fires `app_resume_signal` | Does nothing (Windows has no job control) | Does nothing |
| **After either one** | Reread anything the outside world could have changed | Required | Required after Edit | Required after the fallback editor |
| **Quit** | `self.exit(result, return_code=N)` | Final; Textual restores the terminal | Same | Same (the session ends) |

A redraw only repaints the data the app already has. If the editor changed the file, you have to reread it yourself.

```python
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from textual.app import App, SuspendNotSupported
from textual.binding import Binding


def editor_argv(path: Path) -> list[str]:
    cmd = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if cmd:
        # Windows: posix=False keeps backslashes; strip the surrounding quotes it leaves behind.
        argv = [a.strip('"') for a in shlex.split(cmd, posix=os.name != "nt")]
    else:
        argv = ["notepad"] if os.name == "nt" else ["vi"]
    # Resolve through PATH/PATHEXT so Windows shims like code.cmd are found without a shell.
    argv[0] = shutil.which(argv[0]) or argv[0]
    return [*argv, str(path)]


class DocApp(App[str | None]):
    BINDINGS = [
        Binding("e", "edit", "Edit"),
        Binding("ctrl+z", "suspend_process", "Suspend", show=False),
    ]

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path

    def on_mount(self) -> None:
        self.app_resume_signal.subscribe(self, self._on_resume)
        self.reload_document()

    def _on_resume(self, *_: object) -> None:
        self.reload_document()  # the file may have changed while the app was stopped

    def action_edit(self) -> None:
        try:
            with self.suspend():
                result = subprocess.run(editor_argv(self.path))
        except SuspendNotSupported:
            # Textual Web: there is no local terminal to lend out.
            self.push_screen(InAppEditor(self.path), lambda _saved: self.reload_document())
            return
        except FileNotFoundError:
            self.notify("Editor not found. Set VISUAL or EDITOR.", severity="error")
            return
        if result.returncode != 0:
            self.notify(f"Editor exited with {result.returncode}; file not reloaded.",
                        severity="warning")
            return
        self.reload_document()

    def reload_document(self) -> None:
        ...  # read self.path in a @work worker if it can be large or slow
```

Implementation notes:
- **Blocking is fine here.** `subprocess.run` blocks inside `suspend()` on purpose: the UI is paused and the editor owns the terminal.
- **The editor must wait.** GUI editors return immediately unless told otherwise. Document that users should set `EDITOR="code --wait"` (or `subl -w`). Otherwise you'll reload the file before they've edited it.
- **Ctrl+Z won't clash with undo.** Your Ctrl+Z binding is app-level and not `priority=True`. When the in-app `TextArea` has focus, its own Ctrl+Z undo wins, which is what users expect in an editor.
- **No Windows check is needed.** On Windows and the web, `suspend_process` already does nothing. With `show=False` it also won't show a footer hint that does nothing there.
- **Keep diagnostics off the screen.** Never `print()` while the app is running. Use `self.notify` or `self.log`.

## Exit-code contract

The editor's exit code is in-app state: show it with `notify`, never pass it through as the process's code. Suspending isn't an exit either. Only a final exit sets the code.

| Code | Meaning | How it's set |
|---|---|---|
| `0` | Normal quit or success | `self.exit(result)` |
| `1` | Runtime failure (can't load the document, etc.) | `self.exit(return_code=1)`. Textual also sets 1 on an unhandled exception |
| `2` | Usage error | Raised by the argument parser **before** `app.run()` |
| `130` | User cancelled where a result was expected (picker-style flows only) | `self.exit(None, return_code=130)` |

```python
def main() -> int:
    args = parse_args()  # usage errors exit 2 here, before the UI starts
    app = DocApp(args.path)
    result = app.run()
    if result is not None:
        print(result)  # stdout is safe only after run() returns and the screen is restored
    return app.return_code or 0


if __name__ == "__main__":
    sys.exit(main())
```

`return_code` is only stored on the app object. Unless you call `sys.exit(app.return_code)` as above, the process always exits 0. Under `textual serve`, each browser session is its own process and nobody reads the code. Keep the contract anyway for terminal and script use, but don't put any logic on the web path that depends on it.

## What to test

- **Pilot tests:** Edit with `suspend` patched to raise `SuspendNotSupported` should push the fallback screen. `FileNotFoundError` and a non-zero editor exit should each produce a notification and no reload. A clean edit should reload the file.
- **Exit codes:** after `run_test()`, check `app.return_code` for each way out of the app.
- **One manual PTY check on Unix:** Edit → save → quit the editor → the screen redraws with the new contents. Then Ctrl+Z → `fg` → the screen redraws and the data reloads.
