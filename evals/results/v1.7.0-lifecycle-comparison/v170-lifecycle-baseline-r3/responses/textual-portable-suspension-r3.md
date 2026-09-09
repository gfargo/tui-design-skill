No—don’t `self.exit()`, call `os.system()`, and relaunch. That is a terminal-only workaround, loses app state, and cannot work under Textual Web.

Use two Edit backends:

```python
from pathlib import Path
import subprocess

from textual.app import App

class MyApp(App[None]):
    editor_argv = ["vim"]  # Configure this as argv, not one shell string.
    document_path = Path("document.txt").resolve()

    def action_edit(self) -> None:
        if self.is_web:
            self.open_in_app_editor()       # TextArea/modal, or upload/download flow
            return

        self.save_document()                # Make the file authoritative first.
        try:
            with self.suspend():
                result = subprocess.run(
                    [*self.editor_argv, str(self.document_path)],
                    check=False,
                )
        except OSError as error:
            self.show_editor_error(str(error))
            return

        if result.returncode == 0:
            self.reload_document()
        else:
            self.show_editor_error(
                f"Editor exited with status {result.returncode}"
            )
```

`App.suspend()` restores the terminal while the editor owns it, then restores Textual when the editor exits; it is specifically intended for this use. It is unavailable on Textual Web, so branch on `self.is_web`. [Textual app lifecycle](https://textual.textualize.io/guide/app/), [App API: `is_web`](https://textual.textualize.io/api/app/)

Prefer `subprocess.run([...])` over `os.system(...)`: no shell quoting differences or shell-injection surface, and its return code is directly usable. Require a **foreground, blocking** editor command. A GUI editor that immediately detaches is not a suitable external-edit backend unless its CLI has a “wait” option.

For Ctrl+Z, distinguish two meanings:

- **Undo document edits:** use `TextArea`; `Ctrl+Z` is already its default Undo binding (`Ctrl+Y` redo). Don’t install an app-level priority `ctrl+z` binding that steals it. [TextArea undo/redo](https://textual.textualize.io/widgets/text_area/)
- **Suspend the Unix process:** do not use this as your portable Ctrl+Z behavior. `suspend_process` is a no-op on Windows and Textual Web. [Textual suspension behavior](https://textual.textualize.io/guide/app/)

A clean contract is:

| Channel | Meaning |
|---|---|
| In-app action | `Edit` either opens the local-editor backend or the web/in-app editor backend; it does **not** exit. |
| Editor return code | `0` = reload file; non-zero = retain current UI/session and show an error. |
| `App.exit(result=...)` | Optional in-process result for the launcher, e.g. `"quit"` or `"fatal"`—not an editor handoff. |
| Process exit code | `0` = normal app termination; `1` = unhandled/fatal failure; optionally reserve small non-zero codes (e.g. `2` config, `3` persistence) only when the app truly terminates. |

At the entry point, make Textual’s recorded return code the process status:

```python
if __name__ == "__main__":
    import sys

    app = MyApp()
    app.run()
    raise SystemExit(app.return_code or 0)
```

`self.exit()` ends Textual’s application mode and makes `run()` return; it deliberately does not itself terminate the Python process. [Textual exit and return-code docs](https://textual.textualize.io/guide/app/)
