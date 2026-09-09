Use `tea.ExecProcess`; don’t manually release/restore from `Update`.

```go
type editorDoneMsg struct{ err error }

func openEditor(editorPath, file string) tea.Cmd {
	cmd := exec.Command(editorPath, file) // parse $EDITOR arguments separately
	return tea.ExecProcess(cmd, func(err error) tea.Msg {
		return editorDoneMsg{err: err}
	})
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "e":
			m.notice = "Editing…"
			m.err = nil
			return m, openEditor(m.editorPath, m.file)

		case "q":
			return m, tea.Quit // Run returns nil; normal exit

		case "ctrl+c":
			return m, tea.Interrupt // Run returns tea.ErrInterrupted
		}

	case editorDoneMsg:
		// The editor may have changed the file even if it exited non-zero.
		m.editorErr = msg.err
		m.notice = "Reloading…"
		return m, reloadFile(m.file) // normal async tea.Cmd

	case fileReloadedMsg:
		m.notice = ""
		m.file = msg.file
		if m.editorErr != nil {
			m.err = fmt.Errorf("editor handoff failed: %w", m.editorErr)
		}
	}
	return m, nil
}
```

Lifecycle:

```text
Update → tea.ExecProcess
       → Bubble Tea releases its terminal / stops rendering
       → child receives the real terminal and runs
       → Bubble Tea restores input, terminal modes, and repainting
       → callback creates editorDoneMsg → Update
       → reload externally changed state
```

`ExecProcess` wires the child to Bubble Tea’s terminal, waits for it, restores the TUI, and delivers the callback message. Keep `Program.Run()` alive; do not `defer p.RestoreTerminal()` as program cleanup—`RestoreTerminal` is specifically the counterpart to a temporary `ReleaseTerminal`, while `Run` owns final cleanup. [ExecProcess implementation](https://github.com/charmbracelet/bubbletea/blob/v2.0.8/exec.go#L94-L120), [Release/Restore contract](https://github.com/charmbracelet/bubbletea/blob/v2.0.8/tea.go#L1235-L1281).

Error semantics in v2 are slightly asymmetric:

- Failure to release the terminal: callback receives that error; child was not run.
- Child start/exit failure: Bubble Tea attempts restoration, but callback receives the child error.
- Child succeeds but restoration fails: callback receives the restoration error.
- If both child and restoration fail, the restoration error is currently discarded, so the callback only reports the child error. Treat a callback error as a failed *handoff*, unless you need to implement a custom `tea.ExecCommand` to preserve both errors. [Source](https://github.com/charmbracelet/bubbletea/blob/v2.0.8/exec.go#L94-L120)

For quitting, keep the distinction:

- `q` → `tea.Quit` → clean, intentional exit (usually status 0).
- Raw-mode `Ctrl+C` arrives in `Update` as `tea.KeyPressMsg`; return `tea.Interrupt` so `Run()` returns `tea.ErrInterrupted`. Map that to exit status 130 only after `Run()` returns—never call `os.Exit` from `Update`. [Raw-mode signal behavior](https://github.com/charmbracelet/bubbletea/blob/v2.0.8/tea.go#L599-L635), [interrupt handling](https://github.com/charmbracelet/bubbletea/blob/v2.0.8/tea.go#L713-L720)

While the editor owns the terminal, `q` and `Ctrl+C` belong to the editor, not the TUI. After restoration, raw-mode `Ctrl+C` again becomes Bubble Tea input.

Finally, `$EDITOR` often contains arguments (`nvim -f`); parse it into executable + arguments and append the file path—don’t pass the raw value to `sh -c`.
