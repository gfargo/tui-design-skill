Use `tea.ExecProcess`, not `ReleaseTerminal`/`RestoreTerminal` around `exec.Cmd` yourself. It temporarily hands the terminal to the editor, waits, reclaims terminal modes, repaints, then sends your callback’s message back through `Update`.

```go
import (
	"fmt"
	"os"
	"os/exec"

	tea "charm.land/bubbletea/v2"
)

type editorDoneMsg struct{ err error }

type model struct {
	path   string
	status string
}

func (m model) openEditor() tea.Cmd {
	editor := os.Getenv("VISUAL")
	if editor == "" {
		editor = os.Getenv("EDITOR")
	}
	if editor == "" {
		editor = "vi"
	}

	// Prefer a configured argv in real code if EDITOR may contain arguments.
	cmd := exec.Command(editor, m.path)

	return tea.ExecProcess(cmd, func(err error) tea.Msg {
		return editorDoneMsg{err: err}
	})
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "e":
			return m, m.openEditor()

		case "q":
			// Intentional normal exit: Program.Run returns nil error.
			return m, tea.Quit

		case "ctrl+c":
			// Raw mode delivers this as a key message. Preserve interrupt
			// semantics: Program.Run returns tea.ErrInterrupted.
			return m, tea.Interrupt
		}

	case editorDoneMsg:
		// The terminal has been restored/repainted before this is delivered.
		// Reload anything the editor could have changed; repainting alone
		// does not update this model's data.
		if msg.err != nil {
			m.status = fmt.Sprintf("editor failed: %v", msg.err)
			return m, nil
		}

		m.status = "editor closed"
		return m, reloadFile(m.path)
	}

	return m, nil
}
```

The lifecycle is:

```text
Update → tea.ExecProcess
       → Bubble Tea releases its terminal ownership
       → editor receives stdin/stdout/stderr and runs
       → Bubble Tea restores terminal ownership and redraws
       → callback message → Update resumes with the same model
```

Failure semantics in Bubble Tea v2 are precise:

- If releasing the terminal fails, the callback receives that error.
- If the editor exits with an error, Bubble Tea attempts restoration, but the callback receives the **editor error**.
- If the editor succeeds but restoration fails, the callback receives the **restoration error**.
- The callback only receives `error`, not a failure-origin tag. Treat a non-nil result as a failed handoff; if you need source-level diagnostics, record editor execution details separately or use a controlled wrapper.

For a restoration error, don’t launch further interactive children. Show/record the failure and usually exit cleanly; after `Run` returns, print diagnostics to stderr and choose a non-zero process status from your outer `main`.

Do not add `defer p.RestoreTerminal()` for this. `RestoreTerminal` is the counterpart of a temporary release, not final application cleanup. `Program.Run()` owns final cleanup on `tea.Quit`, interrupts, errors, and its default recovered-panic path.

`q` should mean deliberate, successful quit (`tea.Quit`). In raw mode, Ctrl+C is no longer handled by the terminal driver as SIGINT; Bubble Tea sends `tea.KeyPressMsg`. Return `tea.Interrupt` so callers receive `tea.ErrInterrupted` and can preserve conventional cancellation/exit semantics. If Ctrl+C occurs while the editor owns the terminal, it belongs to the editor and will normally come back as that child’s exit error.  

Sources: Bubble Tea’s [`ExecProcess` implementation](https://github.com/charmbracelet/bubbletea/blob/v2.0.8/exec.go) and [interrupt lifecycle](https://github.com/charmbracelet/bubbletea/blob/v2.0.8/tea.go).
