No—do not `self.exit()`, call `os.system()`, and relaunch. That turns a temporary handoff into a full teardown, loses in-memory state, and cannot work in Textual Web.

Use Textual’s suspension boundary for native terminals:

```python
from pathlib import Path
import subprocess

from textual.app import App, SuspendNotSupported
from textual.binding import Binding

class MyApp(App):
    BINDINGS = [
        Binding("e", "edit", "Edit"),
        # Unix job control only; harmless no-op on Windows and Textual Web.
        Binding("ctrl+z", "suspend_process", "Suspend", show=False),
    ]

    editor_argv = ["vi"]  # Configure as an argv list; e.g. ["code", "--wait"]

    def action_edit(self) -> None:
        if self.is_web:
            self.open_in_app_editor()  # TextArea/modal, or download + upload
            return

        path = self.save_current_document()  # canonical local path
        try:
            with self.suspend():
                result = subprocess.run(
                    [*self.editor_argv, str(path)],
                    check=False,
                )
        except SuspendNotSupported:
            self.open_in_app_editor()
            return
        except FileNotFoundError:
            self.notify("Configured editor was not found.", severity="error")
            return

        # The file may have changed even if the editor returned non-zero.
        self.reload_document(path)
        if result.returncode:
            self.notify(
                f"Editor exited with status {result.returncode}.",
                severity="warning",
            )
```

`self.suspend()` temporarily restores the terminal for the editor, then Textual resumes its UI. Reload the document after it returns; a redraw alone does not reread changed data. Use `subprocess.run(argv)`, not `os.system(string)`, so you avoid shell quoting/injection problems. Textual explicitly documents suspension for launching an editor, but it is unavailable in Textual Web. [Textual app lifecycle](https://textual.textualize.io/guide/app/#suspending)

For Textual Web, there is no server-side route that can launch the browser user’s local editor or access arbitrary local paths. Make “Edit” capability-based:

- Native terminal: external `$EDITOR`/configured editor via `suspend()`.
- Web: an in-app `TextArea` editor, or download the file and allow upload/reload afterward.
- If local external editing is essential, show it as unavailable on Web rather than exiting.

`Ctrl+Z` should mean Unix foreground-process suspension, not undo. Bind Textual’s built-in `suspend_process`; it works on Unix and is intentionally ignored on Windows and Textual Web. Keep undo on a different binding (for example `u`) and let focused text inputs retain their native undo behavior. [Textual’s Ctrl+Z behavior](https://textual.textualize.io/guide/app/#suspending-from-foreground)

Use this exit-code contract:

- `0`: normal app exit—including user cancellation and an editor that failed but was handled in-app.
- `2`: invalid configuration/arguments discovered before or during startup.
- `4`: unrecoverable persistence/domain failure that forces final app exit.
- `1`: unhandled fatal exception (Textual’s default).

An editor’s return code is an operation result, not your app’s process exit code; notify and keep the app alive. Only use `self.exit(return_code=...)` for final termination, then expose it at the process boundary:

```python
if __name__ == "__main__":
    app = MyApp()
    app.run()
    raise SystemExit(app.return_code or 0)
```

Textual restores application mode when `App.exit()` ends the run lifecycle, but it deliberately does not exit the Python process itself. [Textual exit and return-code contract](https://textual.textualize.io/guide/app/#return-code)
