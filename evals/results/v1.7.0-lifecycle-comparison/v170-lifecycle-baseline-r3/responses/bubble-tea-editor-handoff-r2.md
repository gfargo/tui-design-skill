Use `tea.ExecProcess`, not manual `ReleaseTerminal`/`RestoreTerminal` inside `Update`. It owns the whole handoff: release Bubble Tea’s terminal/input, run the child on the real terminal, restore Bubble Tea, then deliver your callback’s message to `Update`.

```go
type editorFinishedMsg struct{ err error }

func openEditor(path string) tea.Cmd {
	editor := os.Getenv("EDITOR")
	if editor == "" {
		editor = "vi"
	}

	// If $EDITOR may contain arguments (for example, "code --wait"),
	// parse/configure it safely rather than passing it as one command name.
	cmd := exec.Command(editor, path)

	return tea.ExecProcess(cmd, func(err error) tea.Msg {
		return editorFinishedMsg{err: err}
	})
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "e":
			return m, openEditor(m.path)

		case "q":
			return m, tea.Quit

		case "ctrl+c":
			// Raw-mode Ctrl-C is a Bubble Tea key event, not SIGINT.
			// Conventionally exit gracefully.
			return m, tea.Quit
		}

	case editorFinishedMsg:
		if msg.err != nil {
			// Keep running and show it, retry, or quit—your policy.
			m.err = msg.err
		}
		return m, nil
	}

	return m, nil
}
```

The lifecycle is:

```text
Update → tea.ExecProcess
       → release terminal / stop Bubble Tea input
       → child uses terminal normally
       → restore terminal / restart Bubble Tea input / repaint
       → editorFinishedMsg{err} → Update
```

`err` is the meaningful result of the handoff:

- If release fails, the callback receives that error.
- If the child fails, Bubble Tea attempts restoration and the callback receives the **child error**.
- If the child succeeds but restoration fails, the callback receives the **restoration error**.
- Consequently, a child error and restoration error are not both surfaced separately by `ExecProcess`; the child error wins.

Do not `defer p.RestoreTerminal()` around a direct `exec.Command.Run()` in `Update`: it bypasses Bubble Tea’s coordinated pause/repaint behavior and makes error/reporting semantics harder to get right. `ExecProcess` is specifically for interactive children such as editors and shells. [Bubble Tea’s exec implementation](https://github.com/charmbracelet/bubbletea/blob/main/exec.go), [official v2 example](https://github.com/charmbracelet/bubbletea/blob/main/examples/exec/main.go)

For termination:

- `q` is just your app’s chosen key binding; return `tea.Quit` if it should quit.
- While Bubble Tea owns the terminal in raw mode, pressing Ctrl-C arrives as `tea.KeyPressMsg` `"ctrl+c"`—not as the terminal-generated `SIGINT`. Handle it explicitly, usually with the same graceful `tea.Quit`.
- While the editor is running, Bubble Tea has restored normal terminal mode. Ctrl-C is then a real interrupt for the foreground child; its resulting nonzero exit is returned through `editorFinishedMsg`, after Bubble Tea attempts restoration.
