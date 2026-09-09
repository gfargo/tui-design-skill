No—don’t `self.exit()`, call `os.system()`, and relaunch. That tears down Textual state and creates avoidable terminal flicker, state loss, and ambiguous editor-error handling.

Use a temporary terminal handoff on native terminals:

```python
from pathlib import Path
import subprocess

from textual.app import App, SuspendNotSupported

class MyApp(App):
    def action_edit(self) -> None:
        path = Path(self.current_path)

        if self.is_web:
            self.open_in_app_editor(path)  # TextArea/modal or browser-native workflow
            return

        try:
            with self.suspend():
                result = subprocess.run(
                    self.editor_argv + [str(path)],  # e.g. ["vim"] or ["notepad.exe"]
                    check=False,
                )
        except SuspendNotSupported:
            self.open_in_app_editor(path)
            return
        except OSError as error:
            self.notify(f"Could not launch editor: {error}", severity="error")
            return

        self.reload_if_changed(path)  # parse/validate, update model, refresh widgets
        if result.returncode:
            self.notify(
                f"Editor exited with status {result.returncode}; changes were reloaded.",
                severity="warning",
            )
```

`App.suspend()` restores the terminal for the child and resumes Textual afterward; it is supported on Unix-like systems and Windows, but not Textual Web. Textual’s own docs use this exact lifecycle for an editor. Prefer `subprocess.run(argv)` to `os.system()`: no shell quoting/injection surprises, and you get a reliable child return code. Store the editor as an argv configuration rather than assuming `$EDITOR` is a single executable; GUI editors may need a wait flag, e.g. `["code", "--wait"]`. [Textual suspend lifecycle](https://textual.textualize.io/guide/app/#suspending), [API support/exception contract](https://textual.textualize.io/api/app/)

The portable contract is:

| Capability | Native Unix | Windows terminal | Textual Web |
|---|---|---|---|
| `Edit` opens local editor | Suspend → run child → reload | Suspend → run child → reload | Not available; use in-app editor/browser flow |
| `Ctrl+Z` | Bind to `suspend_process`; shell resumes with `fg` | No equivalent | No equivalent; preserve browser/text-field undo |
| Reload after handoff | Always reload/check file fingerprint | Same | Reload after in-app save/server update |

For Unix job control, bind Ctrl+Z to Textual’s built-in action:

```python
from textual.binding import Binding

BINDINGS = [
    Binding("e", "edit", "Edit"),
    Binding("ctrl+z", "suspend_process", "Suspend"),
]
```

Textual deliberately disables Ctrl+Z by default; `suspend_process` sends `SIGTSTP` on Unix. It is a no-op on Windows and Textual Web, so capability-gate or hide that binding there—especially on Web, where Ctrl+Z should remain native undo for text input. After any suspend/handoff, treat externally mutable files as stale and reload them; `app_resume_signal` is available for post-suspend work. [Textual’s Ctrl+Z behavior](https://textual.textualize.io/guide/app/#suspending-from-foreground), [built-in action API](https://textual.textualize.io/api/app/)

Keep editor outcomes inside the running app, not as process exits:

- Editor launch failure or nonzero editor status → show an in-app error/warning; reload if the file changed.
- Web local-editor request → use an in-app editor or show a clear “local editor unavailable in web mode” message.
- Only final app shutdown calls `self.exit()`.

Make the final process status explicit at the entry point:

```python
def main() -> None:
    app = MyApp()
    app.run()
    raise SystemExit(app.return_code if app.return_code is not None else 0)
```

Recommended exit-code contract: `0` normal user exit; `1` unexpected/fatal app failure (Textual’s default); `2` invalid startup arguments/configuration; reserve any further codes only for terminal app failures that actually end the session. Do not propagate an editor’s arbitrary exit code as your app’s final status. `App.exit(return_code=...)` records the code but does not itself terminate Python; the wrapper above does. [Textual exit and return-code contract](https://textual.textualize.io/guide/app/#return-code)
