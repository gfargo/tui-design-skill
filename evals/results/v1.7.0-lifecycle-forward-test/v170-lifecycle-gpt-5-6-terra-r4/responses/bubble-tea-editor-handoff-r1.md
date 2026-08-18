Don’t manually `ReleaseTerminal`/`RestoreTerminal` around `exec.Command`. `RestoreTerminal` resumes Bubble Tea’s terminal ownership; it is not final cleanup. Deferring it after `Run()` can put the shell back into TUI modes.

Return `tea.ExecProcess` from `Update` instead:

```go
type editorDoneMsg struct {
	err error
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "e":
			// Prefer a configured executable + args. This simple form assumes
			// $EDITOR is one executable name, not e.g. "nvim -f".
			editor := os.Getenv("EDITOR")
			if editor == "" {
				editor = "vi"
			}

			return m, tea.ExecProcess(
				exec.Command(editor, m.path),
				func(err error) tea.Msg {
					return editorDoneMsg{err: err}
				},
			)

		case "q":
			return m, tea.Quit // normal completion; Run returns nil error

		case "ctrl+c":
			return m, tea.Interrupt // Run returns tea.ErrInterrupted
		}

	case editorDoneMsg:
		// The UI is active again. Render an error in-app, not to stdout.
		m.editorErr = msg.err

		// On successful editing, this is required: a redraw alone still has
		// the old model. Reload asynchronously, then handle its result Msg.
		if msg.err == nil {
			return m, loadFileCmd(m.path)
		}
	}
	return m, nil
}
```

The lifecycle is:

```text
Update → tea.ExecProcess
       → Bubble Tea releases its terminal modes
       → child gets terminal stdin/stdout/stderr and runs
       → Bubble Tea restores terminal modes and redraws
       → callback returns editorDoneMsg → Update
       → reload externally changed state
```

The callback error is how terminal-handoff failures return to `Update`:

- If release fails, the editor is not started and the callback receives that error.
- If the editor fails, Bubble Tea attempts restoration, then the callback receives the editor error.
- If the editor succeeds but restoration fails, the callback receives the restoration error.
- If both the editor and restoration fail, v2 reports the editor error; it does not preserve both separately. Treat the callback error as a generic “editor handoff failed” error unless you deliberately build lower-level instrumentation.

`q` and Ctrl-C should differ:

- `q` → `tea.Quit`: intentional, successful application exit.
- Raw-mode Ctrl-C is a `tea.KeyPressMsg`, not normally an OS signal. Return `tea.Interrupt` so `Program.Run()` returns `tea.ErrInterrupted`; handle that in `main` without `log.Fatal` (typically exit 130 if your CLI exposes exit statuses).
- While the editor is foregrounded, Bubble Tea has released raw mode, so Ctrl-C has normal editor/child-process behavior.

```go
_, err := p.Run()
if errors.Is(err, tea.ErrInterrupted) {
	os.Exit(130)
}
if err != nil {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}
```

Bubble Tea’s `ExecProcess` implementation performs the release, attaches the child’s terminal streams, waits, restores, and sends the callback message back to the program. [v2.0.8 `exec.go`](https://github.com/charmbracelet/bubbletea/blob/v2.0.8/exec.go) The event loop treats `tea.Interrupt` as `tea.ErrInterrupted`; raw-mode Ctrl-C handling is explicitly application-owned. [v2.0.8 `tea.go`](https://github.com/charmbracelet/bubbletea/blob/v2.0.8/tea.go)
