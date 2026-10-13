Don't call `ReleaseTerminal` or run `exec.Command` inside `Update`. Return `tea.ExecProcess` instead and let Bubble Tea handle the handoff. Its result comes back to `Update` as an ordinary message.

## Why the planned approach breaks

1. **It blocks the event loop.** `Update` must stay fast. Waiting on an editor inside it freezes message handling.
2. **`defer p.RestoreTerminal()` isn't cleanup.** `RestoreTerminal` puts Bubble Tea's raw mode, alternate screen and input modes back. It doesn't return the terminal to the shell. `Program.Run()` already does the final restore on normal exit, error and recovered panics.
3. **"Keep using the model" leaves you with stale data.** After the editor exits, a repaint only redraws the old in-memory state. You have to reload what the editor changed.

## The lifecycle

`Update` returns `tea.ExecProcess(cmd, callback)`. Bubble Tea then:
1. pauses input,
2. releases the terminal,
3. connects the editor to the terminal (stdin, stdout, stderr),
4. waits for it to exit,
5. puts its terminal modes back and forces a full repaint,
6. sends your callback message to `Update`.

The callback gets one `error`:

| Outcome | `err` |
|---|---|
| Editor and restore both succeed | `nil` |
| Editor fails to start or exits non-zero | the editor's error |
| Editor succeeds, restore fails | the restore error |
| Both fail | the editor's error (it takes priority) |

```go
package main

import (
	"errors"
	"fmt"
	"os"
	"os/exec"
	"strings"

	tea "charm.land/bubbletea/v2"
)

type editorFinishedMsg struct{ err error }
type fileLoadedMsg struct {
	content string
	err     error
}

type model struct {
	path    string
	content string
	status  string
	editing bool // true while the editor runs; stops a second launch
}

func (m model) Init() tea.Cmd { return loadFile(m.path) }

// Plain file I/O is non-interactive, so it uses an ordinary Cmd, not ExecProcess.
func loadFile(path string) tea.Cmd {
	return func() tea.Msg {
		b, err := os.ReadFile(path)
		return fileLoadedMsg{content: string(b), err: err}
	}
}

func openEditor(path string) tea.Cmd {
	// $EDITOR may carry arguments, e.g. "code --wait" or "nvim -u NONE".
	parts := strings.Fields(os.Getenv("EDITOR"))
	if len(parts) == 0 {
		parts = []string{"vi"}
	}
	c := exec.Command(parts[0], append(parts[1:], path)...)
	return tea.ExecProcess(c, func(err error) tea.Msg {
		return editorFinishedMsg{err: err}
	})
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "ctrl+c":
			// Raw mode delivers Ctrl+C as a key press, not SIGINT.
			return m, tea.Interrupt
		case "q":
			return m, tea.Quit
		case "e":
			if m.editing {
				return m, nil
			}
			m.editing = true
			m.status = "editing…"
			return m, openEditor(m.path)
		}

	case editorFinishedMsg:
		m.editing = false
		var exitErr *exec.ExitError
		switch {
		case msg.err == nil:
			m.status = "saved"
		case errors.As(msg.err, &exitErr):
			// The editor ran but exited non-zero (e.g. vim :cq). The file may still have changed.
			m.status = fmt.Sprintf("editor exited %d", exitErr.ExitCode())
		default:
			// The editor couldn't start (bad $EDITOR, not on PATH), or the editor
			// succeeded and restoring the terminal failed.
			m.status = "editor/terminal error: " + msg.err.Error()
		}
		// Always reload: the disk is the source of truth, and a repaint alone shows stale data.
		return m, loadFile(m.path)

	case fileLoadedMsg:
		if msg.err != nil {
			m.status = "reload failed: " + msg.err.Error()
			return m, nil
		}
		m.content = msg.content
	}
	return m, nil
}

func (m model) View() tea.View {
	v := tea.NewView(m.content + "\n\n" + m.status + "\ne edit · q quit · ctrl+c interrupt")
	v.AltScreen = true
	return v
}

func main() {
	p := tea.NewProgram(model{path: os.Args[1]})
	_, err := p.Run() // Run restores the terminal on every exit path; no defer needed
	switch {
	case errors.Is(err, tea.ErrInterrupted):
		os.Exit(130) // conventional 128+SIGINT
	case err != nil:
		fmt.Fprintln(os.Stderr, err) // safe here: the terminal has already been restored
		os.Exit(1)
	}
}
```

## `q` versus `Ctrl+C`

- **`q` → `tea.Quit`:** a deliberate, successful exit. `Run()` returns `nil`, so the exit status is 0.
- **`Ctrl+C` → `tea.Interrupt`:** in raw mode this arrives as a `tea.KeyPressMsg`, not as a signal. `Run()` returns `tea.ErrInterrupted`, and `main` exits 130 so scripts and shells can tell the user cancelled. Use `tea.Quit` for `Ctrl+C` only if you really want cancel to count as success.
- **Don't call `os.Exit` from `Update`.** It skips the terminal restore that `Run()` performs. Map the error to an exit code in `main`, after `Run()` returns.
- **Ctrl+C while the editor is open belongs to the editor.** Your program's input is paused, so your `ctrl+c` case won't fire. You'll get the result through `editorFinishedMsg`. External SIGINT/SIGTERM, such as `kill`, are already turned into a managed shutdown by Bubble Tea's default signal handler. Don't add your own.
- **Bind `q` to quit only when no text input has focus.** In a text field, `q` should type a `q`; `Ctrl+C` always cancels.

## What to test

- **Unit tests:** feed `editorFinishedMsg{nil}`, `{&exec.ExitError{…}}` and `{errors.New("restore")}` into `Update`. Check the status text, that `editing` resets, and that a reload Cmd comes back. Do the same for `q` and `ctrl+c`, checking that they return `tea.Quit` and `tea.Interrupt`.
- **One PTY smoke test:** use `EDITOR=true` and `EDITOR=false`, then confirm the screen redraws and `stty -a` shows the terminal is sane after `q` and after `Ctrl+C`.
