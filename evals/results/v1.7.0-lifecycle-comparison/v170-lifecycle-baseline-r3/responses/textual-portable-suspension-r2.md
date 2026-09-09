No—don’t call `os.system()` after `self.exit()` from an action, then try to relaunch the app. It mixes UI shutdown, shell parsing, and process control in one handler. In particular, `os.system()` invokes a shell and its status/quoting behavior differs across platforms.

Use this lifecycle instead:

1. The app handles **Edit** as a capability.
2. In a native terminal, suspend Textual, run a configured editor command with `subprocess.run()`, then reload the document.
3. In Textual Web, do not attempt to launch a “local” editor—there is no client-local process capability. Open an in-app `TextArea`/editor screen (or show that external editing is unavailable).
4. Keep `App.exit()` for actual app termination or a deliberate hand-off to an outer CLI coordinator.

Textual’s `suspend()` is designed for temporarily handing the terminal to another application; it is unavailable in Textual Web. [`App.suspend()` guide](https://textual.textualize.io/guide/app/#suspending)

```python
from pathlib import Path
import subprocess

from textual.app import App
from textual.widgets import TextArea


class DocumentApp(App[None]):
    def __init__(self, path: Path, editor_argv: list[str]) -> None:
        super().__init__()
        self.path = path
        self.editor_argv = editor_argv  # e.g. ["nvim"] or ["code", "--wait"]

    def action_edit(self) -> None:
        if self.is_web:
            # Use your own screen/modal containing a TextArea.
            self.push_screen(EmbeddedEditorScreen(self.path))
            return

        try:
            with self.suspend():
                completed = subprocess.run(
                    [*self.editor_argv, str(self.path)],
                    check=False,
                )
        except OSError as error:
            self.notify(f"Could not start editor: {error}", severity="error")
            return

        if completed.returncode:
            self.notify(
                f"Editor exited with status {completed.returncode}",
                severity="error",
            )
            return

        self.reload_document_from_disk()
```

Make `editor_argv` a configured argument list rather than parsing `$EDITOR`; GUI editors must be configured to wait (for example, `code --wait`).

For **Ctrl+Z undo**, use `TextArea` for the web/in-app editor. It already binds Ctrl+Z to undo and Ctrl+Y to redo, including undo history checkpoints. Don’t add an app-wide Ctrl+Z binding that steals that key from the focused editor. [`TextArea` undo/redo](https://textual.textualize.io/widgets/text_area/#undo-and-redo)

If by “Ctrl+Z support” you mean *suspend the terminal process*, that is a different feature:

```python
BINDINGS = [("ctrl+z", "suspend_process", "Suspend")]
```

It is POSIX-only in practice: Textual ignores `suspend_process` on Windows and Textual Web, and it conflicts with editor undo. Don’t make it part of a cross-platform contract. [`suspend_process` behavior](https://textual.textualize.io/guide/app/#suspending-from-foreground)

For an outer-process handoff, use an explicit result—not an exit status—to request editing:

| Condition | `App.exit` result | Process exit code |
|---|---|---:|
| User requests native external edit | `EditRequested(path)` | `0` |
| Normal quit | `None` / `Quit` | `0` |
| Expected fatal app error | optional error result | app-defined nonzero |
| Unhandled exception | — | `1` |

The CLI coordinator may then construct a fresh app after the editor returns:

```python
def main() -> int:
    while True:
        app = DocumentApp(path, editor_argv)
        outcome = app.run()

        if app.return_code not in (None, 0):
            return app.return_code

        if isinstance(outcome, EditRequested):
            status = subprocess.run(
                [*editor_argv, str(outcome.path)], check=False
            ).returncode
            if status:
                return 2  # your documented “editor failed” code
            continue  # reload state and create a fresh app

        return 0
```

`App.exit(result=..., return_code=...)` makes `run()` return the result; Textual leaves process termination to your entry point, where you can return or `sys.exit(app.return_code or 0)`. [`Textual exit and return-code contract`](https://textual.textualize.io/guide/app/#exiting)
