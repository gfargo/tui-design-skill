Don’t manually release/restore the terminal from `Update`. Return `tea.ExecProcess`; it owns the handoff and resumes the same program/model afterward.

```go
type editorFinishedMsg struct{ err error }

func openEditor(file string) tea.Cmd {
	editor := os.Getenv("EDITOR")
	if editor == "" {
		editor = "vi"
	}

	// This assumes EDITOR is one executable name. If you support flags in
	// EDITOR, parse configured argv safely—don’t pass it through a shell.
	cmd := exec.Command(editor, file)

	return tea.ExecProcess(cmd, func(err error) tea.Msg {
		return editorFinishedMsg{err: err}
	})
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "e":
			return m, openEditor(m.file)

		case "q", "ctrl+c":
			return m, tea.Quit
		}

	case editorFinishedMsg:
		if msg.err != nil {
			m.err = msg.err
			// Conservative policy: terminal-handoff failures are fatal.
			return m, tea.Quit
		}

		return m, reloadFile(m.file) // keep using the model
	}

	return m, nil
}
```

The lifecycle is:

```text
Update returns ExecProcess
  → Bubble Tea releases its terminal ownership and stops its input reader
  → child editor runs on that terminal
  → Bubble Tea attempts RestoreTerminal (raw input, reader, repaint)
  → callback creates editorFinishedMsg
  → message is delivered to Update
```

`ExecProcess` is specifically intended for interactive editors/shells and pauses the program until the child exits. It wires the child to the program’s terminal streams and sends the callback result back through `Update`. [API/source](https://github.com/charmbracelet/bubbletea/blob/main/exec.go), [official example](https://github.com/charmbracelet/bubbletea/blob/main/examples/exec/main.go)

Error semantics in the current implementation:

| Event | `editorFinishedMsg.err` |
|---|---|
| Terminal cannot be released | release error |
| Child exits/fails to start | child error; Bubble Tea attempts restoration, but a simultaneous restore error is discarded |
| Child succeeds but restoration fails | restoration error |
| Both child and restore fail | only the child error is returned |

So a non-`nil` callback error is not always “the editor failed.” If terminal restoration fails, continuing the TUI is unreliable; record it and quit conservatively. A normal non-zero editor exit can be made non-fatal if your app recognizes it as a child-process error, but the public callback carries only one unlabelled `error`.

For keys:

- In the Bubble Tea UI, `q` is your app’s explicit quit binding: return `tea.Quit`.
- In Bubble Tea raw mode, `Ctrl+C` is normally a `tea.KeyPressMsg` (`"ctrl+c"`), **not** a kernel SIGINT. Bind it to `tea.Quit` if it should quit the app.
- While the editor is running, Bubble Tea has released the terminal, so neither key reaches `Update`: `q` belongs to the editor, while `Ctrl+C` behaves normally for the foreground editor (usually interrupts it). Its resulting exit error then comes back as `editorFinishedMsg`.

Bubble Tea documents this raw-mode `Ctrl+C` behavior in its signal handling code. [Source](https://github.com/charmbracelet/bubbletea/blob/main/tea.go)
