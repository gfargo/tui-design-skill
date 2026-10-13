**No, don't call `os.system` after `self.exit` and relaunch.** `self.exit()` is the final shutdown. Using it as a temporary handoff causes these problems:

- **Lost state:** the screen stack, undo history, workers, selection and scroll position are all gone.
- **Unclear exit code:** whose exit code does the outer process return, the first app's or the relaunched one's?
- **Shell quoting risk:** `os.system` goes through a shell, so an `$EDITOR` or file path with spaces or metacharacters breaks or gets misinterpreted.
- **Textual Web:** exiting ends the browser session, and the editor would start on the server where nobody can see it.

Textual 8 has a separate API for each of your two needs:

| Need | API | Unix | Windows | Textual Web |
|---|---|---|---|---|
| Edit in a local editor | `with self.suspend(): subprocess.run(argv)` | ✅ | ✅ | raises `SuspendNotSupported`, so use an in-app fallback |
| Ctrl+Z | `suspend_process` action | ✅ SIGTSTP, resumes on `fg` | no-op | no-op |

Neither one replaces exit. After either kind of suspend, the app keeps running, and you reload any data the editor or shell might have changed. Textual repaints the screen on resume but doesn't re-read your files.

## Lifecycle

```python
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from textual.app import App, ComposeResult, SuspendNotSupported
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Footer, TextArea

EXIT_OK, EXIT_ERROR, EXIT_USAGE, EXIT_INTERRUPTED = 0, 1, 2, 130


def editor_argv(path: Path) -> list[str] | None:
    raw = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    argv = shlex.split(raw, posix=os.name != "nt") if raw else (
        ["notepad"] if os.name == "nt" else ["vi"]
    )
    exe = shutil.which(argv[0].strip('"'))  # resolves code.cmd etc. on Windows
    return [exe, *argv[1:], str(path)] if exe else None


class EditScreen(ModalScreen[str | None]):
    """Fallback for Textual Web or a missing editor."""
    BINDINGS = [("ctrl+s", "save", "Save"), ("escape", "cancel", "Cancel")]

    def __init__(self, text: str) -> None:
        super().__init__()
        self._text = text

    def compose(self) -> ComposeResult:
        yield TextArea(self._text)  # TextArea binds ctrl+z to undo
        yield Footer()

    def action_save(self) -> None:
        self.dismiss(self.query_one(TextArea).text)

    def action_cancel(self) -> None:
        self.dismiss(None)


class NotesApp(App[None]):
    BINDINGS = [
        Binding("e", "edit", "Edit"),
        Binding("ctrl+z", "suspend_process", "Suspend"),  # not priority=True
        Binding("q", "quit_ok", "Quit"),
    ]

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path

    def on_mount(self) -> None:
        self.app_resume_signal.subscribe(self, self._on_resume)
        self.reload()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "suspend_process":
            # Hide and disable where it would silently do nothing.
            return not (sys.platform == "win32" or self.is_web)
        return True

    def action_edit(self) -> None:
        text = self.path.read_text(encoding="utf-8")
        # Close the file before the editor opens it; Windows locks open files.
        fd, name = tempfile.mkstemp(suffix=self.path.suffix, text=True)
        tmp = Path(name)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        try:
            argv = editor_argv(tmp)
            if argv is None:
                self.notify("No editor found; using built-in editor", severity="warning")
                self.push_screen(EditScreen(text), self._apply)
                return
            try:
                with self.suspend():
                    result = subprocess.run(argv)  # argv list, no shell
            except SuspendNotSupported:  # Textual Web
                self.push_screen(EditScreen(text), self._apply)
                return
            if result.returncode != 0:
                self.notify(f"Editor exited {result.returncode}; no changes saved",
                            severity="error")
                return
            self._apply(tmp.read_text(encoding="utf-8"))
        finally:
            tmp.unlink(missing_ok=True)

    def _apply(self, new_text: str | None) -> None:
        if new_text is None:
            return
        self.path.write_text(new_text, encoding="utf-8")
        self.reload()

    def _on_resume(self, _app: App) -> None:
        self.reload()  # a shell session during Ctrl+Z may have changed the file

    def reload(self) -> None:
        ...  # re-read self.path into your widgets/reactives

    def action_quit_ok(self) -> None:
        self.exit(return_code=EXIT_OK)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()  # exits 2 on usage errors
    app = NotesApp(args.path)
    app.run()
    return app.return_code or EXIT_OK  # return_code is None if never set


if __name__ == "__main__":
    sys.exit(main())
```

Notes on the code:

- **GUI editors** like VS Code or Sublime return immediately unless told to wait. Tell users to set something like `EDITOR="code --wait"`. Otherwise you'll read the temp file before they've edited it.
- **Blocking call:** `subprocess.run` blocks the event loop during the edit. That's acceptable here because the UI is paused and the editor owns the terminal, but timers and workers also pause until it returns. Large reloads after the edit should go in a worker.
- **Ctrl+Z conflict:** `TextArea` uses Ctrl+Z for undo. Keep the app's suspend binding non-priority so a focused text area wins. Otherwise suspend breaks undo in the fallback editor.
- **Hidden when unsupported:** `check_action` removes Suspend from the footer on Windows and Web, so you never show a key that does nothing.

## Exit-code contract

Only final shutdown sets the process exit code. Editor results and suspend/resume never do.

| Situation | Process exit | App behavior |
|---|---|---|
| User quits normally | `0` | `self.exit(return_code=0)` |
| Unhandled exception | `1` | Textual cleans up the terminal and sets `return_code` to 1 |
| Bad arguments, before the UI starts | `2` | argparse handles it; no UI is drawn |
| User cancels or interrupts, if you bind one | `130` | `self.exit(return_code=130)` |
| Editor exits non-zero | n/a | Notify, discard the edit, keep running |
| Editor not found | n/a | Notify and fall back to `EditScreen` |
| Textual Web, Edit action | n/a | `SuspendNotSupported`, fall back to `EditScreen` |
| Ctrl+Z, then `fg` | n/a | Same process; `app_resume_signal` triggers a reload |
| Ctrl+Z on Windows or Web | n/a | Action disabled and hidden |
| SIGKILL | `137`, set by the shell | No cleanup is possible |

Rules that keep it portable:

1. Call `sys.exit(app.return_code or 0)` once, in `main()`. `return_code` is only a value stored on the app; the process doesn't return it unless you pass it on.
2. Keep codes in the range 0–255. Windows allows more, but POSIX shells truncate.
3. Don't map an editor's exit status onto your app's exit status. They're different processes with different meanings.
4. Don't add your own SIGTSTP or SIGCONT handlers. `suspend_process` and `app_resume_signal` already handle them, and they don't exist on Windows.

## Tests worth having

- **Unit tests:** `editor_argv` with `VISUAL`/`EDITOR` set, unset, quoted, or pointing to a missing binary, under both `os.name` values.
- **Pilot tests:** monkeypatch `App.suspend` to raise `SuspendNotSupported` and check that `EditScreen` opens. Then monkeypatch `subprocess.run` to return 0 and 1, and check that the file is saved or left unchanged.
- **One PTY smoke test on Unix:** press `e` with `EDITOR` set to a script that appends a line and exits. Then press Ctrl+Z, run `fg`, and check the redraw. Finally press `q` and check that the exit code is 0 and the terminal mode is restored.
