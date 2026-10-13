No. Don't call `os.system` after `self.exit()` and then relaunch the app. Textual already has a supported way to do this: `App.suspend()`. That approach has these problems:

- **Textual Web:** the editor would start on the server, not on the user's machine. The browser user never sees it.
- **Lost state:** relaunching throws away the screen stack, focus, scroll position, undo history and running workers. You'd have to save and restore all of it by hand.
- **Terminal glitches:** tearing down and restarting the terminal setup causes flicker, and on Windows consoles you can get leftover mouse and alt-screen modes.
- **Unclear exit codes:** you get the editor's code, the app's code and the relaunched app's code, and no clear rule for which one the process should return.

## Lifecycle

```
running ──Edit──▶ suspend() ──▶ editor runs on the real TTY ──▶ resume ──▶ reload file ──▶ running
   │                 │
   │                 └─ SuspendNotSupported (Textual Web, …) ──▶ in-app TextArea editor modal
   │
   ├─Ctrl+Z (POSIX terminal only)──▶ SIGTSTP ──▶ shell job control ──▶ fg ──▶ running
   │
   └─quit / fatal error──▶ self.exit(result, return_code) ──▶ main() ──▶ sys.exit(return_code)
```

The rules:

1. **Always suspend in place, never relaunch.** Use `with self.suspend():` to hand the terminal to the editor. Textual restores the terminal and redraws when the block ends.
2. **Decide what's possible by catching the error, not by checking the platform.** `suspend()` raises `textual.app.SuspendNotSupported` when the driver can't suspend, which includes Textual Web. Catch it and fall back to an in-app editor. Don't test `sys.platform`.
3. **Ctrl+Z is POSIX-terminal only.** Bind it to the built-in `suspend_process` action, and use `check_action` to hide the binding on Windows and Web.
4. **Watch for the Ctrl+Z conflict.** `TextArea` uses Ctrl+Z for undo. Don't make your binding `priority=True`, or users will lose undo inside text areas.
5. **Only `main()` turns the result into a process exit code.**

## Code sketch

```python
import os, shlex, signal, subprocess, sys, tempfile
from pathlib import Path

from textual.app import App, SuspendNotSupported
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import TextArea

WINDOWS = sys.platform == "win32"


def editor_command() -> list[str]:
    raw = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if not raw:
        return ["notepad"] if WINDOWS else ["vi"]
    # GUI editors need a wait flag, e.g. EDITOR="code --wait"
    return shlex.split(raw, posix=not WINDOWS)


class InAppEditor(ModalScreen[str | None]):
    BINDINGS = [("ctrl+s", "save", "Save"), ("escape", "cancel", "Cancel")]

    def __init__(self, text: str) -> None:
        super().__init__()
        self._text = text

    def compose(self):
        yield TextArea(self._text, id="body")

    def action_save(self) -> None:
        self.dismiss(self.query_one(TextArea).text)

    def action_cancel(self) -> None:
        self.dismiss(None)


class MyApp(App[None]):
    BINDINGS = [
        Binding("e", "edit", "Edit"),
        Binding("ctrl+z", "suspend_process", "Suspend"),  # not priority: TextArea undo wins when focused
    ]

    def check_action(self, action: str, parameters) -> bool | None:
        if action == "suspend_process":
            return not WINDOWS and not self.is_web
        return True

    def action_edit(self) -> None:
        original = self.current_text()
        try:
            new = self._edit_external(original)
        except SuspendNotSupported:
            self.push_screen(InAppEditor(original), self._apply_edit)
            return
        self._apply_edit(new)

    def _edit_external(self, text: str) -> str | None:
        # delete=False: on Windows, an open NamedTemporaryFile can't be reopened by another process
        fd, name = tempfile.mkstemp(suffix=".txt")
        path = Path(name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            with self.suspend():  # raises SuspendNotSupported before touching the terminal
                rc = subprocess.run([*editor_command(), str(path)]).returncode
            if rc != 0:
                self.notify(f"Editor exited with {rc}; changes discarded", severity="warning")
                return None
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self.notify("No editor found; set $VISUAL or $EDITOR", severity="error")
            return None
        finally:
            path.unlink(missing_ok=True)

    def _apply_edit(self, new: str | None) -> None:
        if new is not None and new != self.current_text():
            self.set_text(new)

    def current_text(self) -> str: ...
    def set_text(self, text: str) -> None: ...


def main() -> int:
    app = MyApp()
    try:
        app.run()
    except KeyboardInterrupt:
        return 130
    return app.return_code or 0


if __name__ == "__main__":
    sys.exit(main())
```

Notes on the sketch:

- Calling `subprocess.run` inside `suspend()` blocks the event loop on purpose. The app is suspended at that point, so it isn't drawing anything. Call it from the action handler, not from a thread worker.
- Re-read the file after the editor closes. Some editors save by replacing the file rather than writing into it.

## Exit-code contract

| Code | Meaning | Who sets it |
|---|---|---|
| `0` | Normal quit | `self.exit()` |
| `1` | Unhandled exception (Textual prints the traceback) | Textual sets this automatically |
| `2` | Bad CLI usage or config, found before the UI starts | `main()`, before `app.run()` |
| `3+` | Your own app-level failures, e.g. `self.exit(return_code=3, message="…")` | the app, documented per code |
| `130` | Interrupted (SIGINT reached the process) | `main()` |

The editor's exit code never becomes the process exit code. A non-zero editor exit only means "discard this edit and show a notice". The app keeps running.

## If you really need to run something after the app closes

For example, an "open in editor and quit" command. Return what you want done as the app's result with `self.exit(result=...)`. Then let `main()` run it after `app.run()` returns, and use that command's exit code. Make it the last thing the process does, not a relaunch. On Textual Web, turn this option off. For downloads there, use the app's file-delivery APIs.

I wrote this from my knowledge of the Textual API and haven't run it against Textual 8. Check the exact names in your installed version: `SuspendNotSupported`, `is_web`, `action_suspend_process` and `return_code`.
