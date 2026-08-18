No—don’t `self.exit()`, call `os.system()`, and relaunch for the normal Edit path. Keep one app session and temporarily lend the terminal to the editor:

```python
import subprocess
from textual.app import App, SuspendNotSupported

class MyApp(App[None]):
    def action_edit(self) -> None:
        target = self.document_path
        argv = [*self.editor_argv(), str(target)]  # configure as argv, not a shell string

        try:
            with self.suspend():
                result = subprocess.run(argv, check=False)
        except SuspendNotSupported:
            self.open_in_app_editor()  # or download/upload or a remote-editor flow
            return

        # The editor may have written changes even if it returned non-zero.
        self.reload_document_from_disk()
        if result.returncode:
            self.notify(f"Editor exited with {result.returncode}", severity="warning")
```

`App.suspend()` restores the terminal for the child and restores Textual when it returns; it works in local Unix and Windows terminals, but raises `SuspendNotSupported` in Textual Web. Use `subprocess.run(argv)`, not `os.system`, so there is no shell quoting/injection contract to maintain. Textual documents this exact suspend-and-editor lifecycle. [App guide](https://textual.textualize.io/guide/app/)

Lifecycle contract:

1. `e` / **Edit** checks the runtime capability.
2. Local terminal: suspend → launch local editor inheriting stdio → resume.
3. After resume: reread and validate the file; a redraw alone does not reload external changes.
4. Textual Web: never spawn an editor on the server. Offer an in-app editor, import/export, or an explicitly configured browser-accessible editor.
5. An editor failure is an in-session outcome, not a reason to relaunch or terminate the app.

For Ctrl+Z, decide which meaning you need:

- **Foreground job-control support:** bind `ctrl+z` to Textual’s `suspend_process`. On Unix it sends `SIGTSTP`; on Windows and Textual Web it is intentionally a no-op. Only show the shortcut in local Unix terminal help. [Textual App API](https://textual.textualize.io/api/app/)
- **Application undo:** don’t use Ctrl+Z as a cross-platform TUI binding—it conflicts with Unix suspend. Use `z` for undo and a visible command/help entry; maintain an action stack or snapshots. Let text fields retain their native editing behavior.

Keep process exit codes separate from edit outcomes:

| Code | Contract |
|---:|---|
| 0 | Normal user exit, including a canceled/failed editor session that the app handled |
| 2 | CLI/configuration usage error before the UI can run |
| 65 | Unrecoverable document/input validation failure |
| 70 | Unexpected fatal application failure |

Do not propagate the editor’s exit code as your app’s exit code; report it, reload if the file changed, and keep the session alive. At the process boundary:

```python
def main() -> int:
    app = MyApp()
    app.run()
    return app.return_code or 0

if __name__ == "__main__":
    raise SystemExit(main())
```

`self.exit(return_code=...)` is for final process outcomes, not temporary handoff; Textual exposes `app.return_code` specifically for the outer `sys.exit(...)` call.
