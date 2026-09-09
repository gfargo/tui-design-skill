Use `tea.ExecProcess`, not `ReleaseTerminal`/`RestoreTerminal` from `Update`. It keeps the same program and model alive while Bubble Tea performs the temporary terminal handoff.

```go
type editorDoneMsg struct{ err error }

func openEditor(path string) tea.Cmd {
	// Parse/configure EDITOR arguments separately; don't pass an unparsed
	// "$EDITOR file" string to exec.Command.
	cmd := exec.Command(editorBinary, path)

	return tea.ExecProcess(cmd, func(err error) tea.Msg {
		return editorDoneMsg{err: err}
	})
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "e":
			m.status = "Editing…"
			return m, openEditor(m.path)

		case "q":
			return m, tea.Quit // normal exit

		case "ctrl+c":
			return m, tea.Interrupt // interrupted exit
		}

	case editorDoneMsg:
		// Reload even when err != nil: an editor can save changes and still
		// exit non-zero (or be interrupted).
		m.lastEditorErr = msg.err
		return m, reloadFile(m.path)

	case fileReloadedMsg:
		if msg.err != nil {
			m.status = "Reload failed: " + msg.err.Error()
		} else if m.lastEditorErr != nil {
			m.status = "Editor ended: " + m.lastEditorErr.Error()
		} else {
			m.status = "Reloaded"
		}
	}
	return m, nil
}
```

The lifecycle is:

```text
Update("e")
  → tea.ExecProcess
  → Bubble Tea releases its terminal modes
  → editor owns the terminal and exits
  → Bubble Tea restores modes and redraws
  → callback sends editorDoneMsg
  → Update reloads externally changed state
```

`ExecProcess` attaches the child to the terminal, waits for it, restores Bubble Tea’s terminal state, and sends your callback message back through `Update`. It is specifically intended for interactive editors and shells; ordinary background I/O should use a normal `tea.Cmd`. [Bubble Tea’s ExecProcess implementation](https://raw.githubusercontent.com/charmbracelet/bubbletea/v2.0.8/exec.go)

Failure semantics in v2 are important:

| Event | `editorDoneMsg.err` |
|---|---|
| Release fails | release error |
| Child exits with an error | child error; Bubble Tea still attempts restoration |
| Child succeeds, restoration fails | restoration error |
| Both child and restoration fail | child error; the restoration error is not exposed by this helper |

So treat a non-nil callback error as “the handoff did not complete cleanly,” reload if feasible, and retain/show it. Don’t assume `ExecProcess` lets you reliably distinguish a child error from a restore error without additional application-specific wrapping.

For exit keys:

- `q` → `tea.Quit`: intentional normal quit; `Program.Run()` returns `nil`.
- Raw-mode `Ctrl+C` arrives as `tea.KeyPressMsg`, not automatically as a Unix signal. Return `tea.Interrupt` so Bubble Tea performs cleanup and `Run()` returns `tea.ErrInterrupted`.
- Do not call `os.Exit` in `Update`. Map `ErrInterrupted` to your desired process status after `Run()` returns—commonly 130.

```go
func main() {
	_, err := tea.NewProgram(newModel()).Run()

	switch {
	case err == nil:
		return
	case errors.Is(err, tea.ErrInterrupted):
		os.Exit(130)
	default:
		fmt.Fprintln(os.Stderr, err) // terminal is restored now
		os.Exit(1)
	}
}
```

If `Ctrl+C` is pressed while the editor owns the foreground terminal, it is the editor’s interrupt to handle; when the editor exits, its result returns through `editorDoneMsg`. Bubble Tea’s `Quit` and `Interrupt` paths are distinct: the former ends normally, while the latter makes `Run()` return `ErrInterrupted`. [Bubble Tea event-loop source](https://raw.githubusercontent.com/charmbracelet/bubbletea/v2.0.8/tea.go)
