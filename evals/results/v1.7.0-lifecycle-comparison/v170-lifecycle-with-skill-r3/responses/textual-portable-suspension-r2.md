No—don’t `self.exit()`, call `os.system()`, and relaunch for the normal Edit flow. That needlessly loses in-memory state and is impossible to make meaningful in Textual Web.

Use Textual’s suspend lifecycle in a local terminal:

```python
import os
import subprocess
from pathlib import Path

from textual.app import App, SuspendNotSupported
from textual.binding import Binding


class MyApp(App[None]):
    BINDINGS = [
        Binding("e", "edit", "Edit"),
        Binding("ctrl+z", "suspend_process", "Suspend", show=False),
    ]

    def action_edit(self) -> None:
        path = Path("document.txt").resolve()

        if self.is_web:
            self.notify("Local editor is unavailable in the web app.", severity="warning")
            # Open an in-app TextArea/modal instead.
            return

        editor = (
            [os.environ["VISUAL"]]
            if os.environ.get("VISUAL")
            else [os.environ.get("EDITOR", "notepad.exe" if os.name == "nt" else "vi")]
        )

        try:
            with self.suspend():
                completed = subprocess.run(
                    [*editor, str(path)],
                    check=False,
                )
        except SuspendNotSupported:
            self.notify("This runtime cannot launch a local editor.", severity="warning")
            return
        except FileNotFoundError:
            self.notify(f"Editor not found: {editor[0]}", severity="error")
            return

        if completed.returncode == 0:
            self.reload_from_disk(path)
        else:
            self.notify(
                f"Editor exited with status {completed.returncode}; changes not reloaded.",
                severity="warning",
            )
```

`App.suspend()` restores the terminal, gives the editor exclusive terminal control, then resumes and redraws your app. It is supported on Unix-like systems and Windows, but deliberately unavailable in Textual Web. [`App.suspend` API](https://textual.textualize.io/api/app/), [Textual’s editor example](https://textual.textualize.io/guide/app/#suspending)

For `Ctrl+Z`:

- On Unix TTYs, bind it to `suspend_process` as above. Textual cleanly suspends and resumes the foreground process.
- On Windows and Textual Web, that action is intentionally ignored—there is no Unix job-control equivalent. Don’t promise “suspend” there.
- If you mean **undo**, don’t install a global `Ctrl+Z` binding. Let a focused `TextArea` own it; otherwise use a separate application undo binding such as `u`.

A portable contract:

| Event | TTY app | Windows | Textual Web |
|---|---|---|---|
| Edit | Suspend → `subprocess.run()` → resume/reload | Same | In-app editor or upload/download flow |
| Ctrl+Z | Suspend process | No-op | Preserve text-field undo; otherwise no-op |
| Editor failure | Show UI error; keep app alive | Same | Not applicable |

For process exit codes, reserve them for the **actual app process**, not ordinary Edit results:

- `0`: normal user exit, including an editor that was cancelled or failed after the app showed an error.
- `1`: unhandled Textual failure (Textual’s default).
- `2+`: documented fatal application conditions only, e.g. unrecoverable configuration or persistence failure.

Call `self.exit(return_code=...)` only when the session really ends; it stops Textual but does not itself terminate Python. At your true entry point, propagate the code once with `sys.exit(app.return_code or 0)`. [`App.exit` and return-code behavior](https://textual.textualize.io/guide/app/#return-code)

If you ever deliberately choose an exit-and-relaunch architecture—for example, a tiny picker rather than a persistent app—make it an outer launcher loop with explicit result data. But for a full Textual session, suspension is the right lifecycle.
