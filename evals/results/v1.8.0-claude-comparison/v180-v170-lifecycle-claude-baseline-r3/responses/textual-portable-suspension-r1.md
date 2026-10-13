No. Don't exit and relaunch. Textual has a built-in way to do this: `App.suspend()` for the editor and `action_suspend_process` for Ctrl+Z. Exiting and relaunching would:

- **Lose state**: the screen stack, scroll positions, undo history and workers are all gone.
- **Break Textual Web**: `exit()` ends the browser session, so there is nothing to relaunch into. The editor would also run on the server, not in front of the user.
- **Cause Windows problems**: `os.system` goes through `cmd.exe`, so quoting breaks and the editor's exit status is unreliable.
- **Flicker the screen and mix up exit codes**: the process exit code ends up describing the editor or the relaunch, not your app.

## Lifecycle

| Situation | Edit action | Ctrl+Z |
|---|---|---|
| Unix terminal | `with self.suspend():` then run the editor, then reload the file | `action_suspend_process` sends SIGTSTP and the app redraws on `fg` |
| Windows terminal | `with self.suspend():` then run the editor (this works) | Does nothing, so hide the binding |
| Textual Web | `SuspendNotSupported`, so fall back to an in-app `TextArea` editor | Does nothing, so hide the binding |

Ctrl+Z is not bound by default, so you have to add the binding yourself. A focused `TextArea` already uses Ctrl+Z for **undo**, and the focused widget's binding wins. Decide which meaning you want. A common choice is to keep undo inside editors and suspend everywhere else.

```python
import os, shlex, shutil, subprocess, sys
from pathlib import Path

from textual.app import App, SuspendNotSupported
from textual.binding import Binding

# Exit-code contract (see below)
EXIT_OK, EXIT_ERROR, EXIT_USAGE, EXIT_INTERRUPTED = 0, 1, 2, 130


def editor_command(path: Path) -> list[str] | None:
    """Resolve $VISUAL/$EDITOR into argv with no shell. Returns None if no editor is found."""
    for var in ("VISUAL", "EDITOR"):
        if cmd := os.environ.get(var):
            return [*shlex.split(cmd, posix=(os.name != "nt")), str(path)]
    fallback = "notepad" if os.name == "nt" else "vi"
    return [fallback, str(path)] if shutil.which(fallback) else None


class MyApp(App[int]):
    BINDINGS = [
        Binding("e", "edit", "Edit"),
        Binding("ctrl+z", "suspend_process", "Suspend"),
    ]

    def check_action(self, action: str, parameters) -> bool | None:
        if action == "suspend_process":
            # Only works under a real Unix TTY. Elsewhere, hide it from the footer
            return not (self.is_web or sys.platform == "win32")
        return True

    def action_edit(self) -> None:
        path = self.current_path  # whatever your app is editing
        cmd = editor_command(path)
        if cmd is None:
            self.notify("No editor found; set $VISUAL or $EDITOR", severity="error")
            return
        try:
            with self.suspend():  # restores the terminal, then redraws on exit
                result = subprocess.run(cmd)  # blocking is fine; the app is suspended
        except SuspendNotSupported:  # Textual Web, or no controlling terminal
            self.open_inline_editor(path)  # e.g. push a ModalScreen holding a TextArea
            return
        except OSError as exc:  # editor binary missing or not executable
            self.notify(f"Editor failed to start: {exc}", severity="error")
            return
        if result.returncode != 0:
            self.notify(f"Editor exited with {result.returncode}; changes not loaded",
                        severity="warning")
            return
        self.reload_from_disk(path)  # re-read the file and refresh widgets


def main() -> None:
    app = MyApp()
    app.run()
    sys.exit(app.return_code if app.return_code is not None else EXIT_ERROR)
```

Notes:
- Run `suspend()` from the app's own thread, meaning inside an action or handler, not from a threaded worker.
- Never use `os.startfile` or `start`. They don't block, so you can't tell when editing is finished.
- Pass a list of arguments and no shell. That avoids quoting bugs on both platforms. Editors like VS Code need `code --wait`, which users already set in `$EDITOR`.

## Exit-code contract

Only the app's own exit sets the process exit code. Editor failures never do.

| Code | Meaning | How it's set |
|---|---|---|
| `0` | Normal quit | `self.exit()` or `self.exit(return_code=0)` |
| `1` | Unhandled error | Textual sets this itself when a crash ends the app |
| `2` | Bad arguments or config, found before or at mount | `self.exit(return_code=2, message="…")` |
| `130` | Interrupted by the user (Ctrl+C style abort) | `self.exit(return_code=130)` |

Rules:
1. **An editor's non-zero status is a UI event.** Show it with `notify()` and keep running.
2. **Suspend and resume are not exits.** No code is produced, and the app keeps running with its state intact.
3. **On Textual Web, an exit ends the session.** The code goes to the server process, not to the browser user. So a code means nothing on its own here; show the user a message before exiting.
4. **The process exits through `sys.exit(app.return_code)` in one place** (`main`). Never call `os._exit` and never relaunch.
