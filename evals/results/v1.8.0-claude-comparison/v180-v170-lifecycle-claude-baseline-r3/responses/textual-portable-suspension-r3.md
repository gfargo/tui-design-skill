**Short answer: no.** Calling `self.exit()`, then `os.system(editor)`, then relaunching the app throws away all in-memory state: screens, scroll position, undo history and workers. It also makes the screen flash. On Textual Web it fails outright, because when the process exits the browser session ends and nothing comes back. On Windows, `os.system` sends the command through `cmd.exe`, so paths with spaces get quoted wrong. Textual already has a built-in way to do this: `App.suspend()`.

## Lifecycle

| Situation | Edit action | Ctrl+Z |
|---|---|---|
| Unix terminal | `with self.suspend():` run the editor and wait for it | `action_suspend_process` sends SIGTSTP, so `fg` resumes the app |
| Windows terminal | `with self.suspend():` works with the Windows driver | Does nothing (no job control). Hide the binding or show a notice |
| Textual Web / headless | `suspend()` raises `SuspendNotSupported`, so open an editor inside the app instead | Does nothing |

Rules:
1. **The app process never exits to edit.** It suspends, runs the editor as a blocking child process, then resumes and redraws.
2. **The editor's exit code is not the app's exit code.** If the editor fails, show a notification and keep the app running.
3. **Detect changes by comparing file content** (hash or mtime), not by looking at the editor's exit status.
4. **Always provide a fallback.** If suspending isn't supported, use a `TextArea` screen inside the app.

## Code

```python
import hashlib, os, shlex, subprocess, sys
from pathlib import Path

from textual.app import App, SuspendNotSupported
from textual.binding import Binding


def editor_argv(path: Path) -> list[str]:
    cmd = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if not cmd:
        cmd = "notepad" if sys.platform == "win32" else "vi"
    # GUI editors must block: e.g. EDITOR="code --wait"
    return [*shlex.split(cmd, posix=(os.name != "nt")), str(path)]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


class MyApp(App):
    BINDINGS = [
        Binding("e", "edit", "Edit"),
        # Not priority: a focused TextArea keeps Ctrl+Z for undo.
        Binding("ctrl+z", "suspend_process", "Suspend", show=sys.platform != "win32"),
    ]

    def on_mount(self) -> None:
        # Fires after SIGCONT (fg) and after suspend() returns.
        self.app_resume_signal.subscribe(self, lambda _: self.refresh_from_disk())

    def action_edit(self) -> None:
        path = self.current_path()
        before = digest(path)
        try:
            with self.suspend():
                rc = subprocess.run(editor_argv(path)).returncode
        except SuspendNotSupported:          # Textual Web, headless, etc.
            self.push_screen(InAppEditor(path), callback=lambda _: self.refresh_from_disk())
            return
        except FileNotFoundError as e:       # editor binary missing
            self.notify(f"Editor not found: {e.filename}", severity="error")
            return

        if rc != 0:
            self.notify(f"Editor exited with {rc}; changes may not be saved", severity="warning")
        if digest(path) != before:
            self.refresh_from_disk()
```

Notes:
- **Blocking is fine here.** The event loop waits while the terminal belongs to the editor. Don't run the editor in a thread worker, because `suspend()` has to be called on the app's thread.
- **GUI editors need a wait flag** (`code --wait`, `subl -w`). Otherwise the editor returns immediately and you resume with the file unchanged.
- **Don't run Ctrl+Z as a priority binding.** `TextArea` uses Ctrl+Z for undo, so let the focused widget handle it first.
- **Ctrl+Z inside a `TextArea`.** If you want Ctrl+Z to suspend even there, bind suspend to another key as well.

## Exit-code contract

Set the process exit code from the app's result. Don't call `sys.exit` inside handlers.

```python
def main() -> int:
    app = MyApp()
    app.run()
    return app.return_code or 0

if __name__ == "__main__":
    sys.exit(main())
```

| Code | Meaning | How it's produced |
|---|---|---|
| `0` | Normal quit | `self.exit()` |
| `1` | Unhandled exception / crash | Textual sets this automatically |
| `2` | Bad CLI usage or config | Checked before `app.run()` |
| `3+` | App-specific outcomes (e.g. "user aborted with unsaved changes") | `self.exit(result, return_code=3)` |
| `130` | Interrupted (SIGINT) | Optional, if you handle Ctrl+C yourself |

The editor's exit code, a suspend/resume cycle and the web fallback never change the process exit code. Only an intentional `self.exit(...)` or a crash does.

I haven't checked this against an installed Textual 8; there's no code or environment in the working directory. The APIs it relies on are long-standing: `App.suspend`, `SuspendNotSupported`, `action_suspend_process`, `app_resume_signal` and `return_code`. Still, test the Windows `suspend()` path on a real Windows terminal before you ship.
