Your plan has two problems:

- **The program is blocked while the editor runs.** `Update` runs on the event loop. If it calls `exec.Command(...).Run()` directly, the loop stops for as long as the editor is open, and anything that calls `p.Send` waits too.
- **You lose the restore error.** With `defer p.RestoreTerminal()`, its error is dropped and never reaches the model.

Use `tea.ExecProcess` instead. `Update` returns a `Cmd`, and the event loop runs the child for you. I checked this in `charm.land/bubbletea/v2@v2.1.0/exec.go` and `tea.go`:

1. `Update` returns `tea.ExecProcess(cmd, callback)`. That produces an internal `execMsg`.
2. The event loop handles `execMsg` with `p.exec(...)` (`tea.go:858`, commented "NB: this blocks"). That is the correct place to block.
3. `releaseTerminal` sets `ignoreSignals = 1`, stops reading input, and leaves raw mode and the alt screen.
4. The child gets the program's input and output, with stderr going to `os.Stderr`, unless you set your own.
5. It then calls `RestoreTerminal()`, which sets `ignoreSignals = 0`, returns to raw mode and redraws.
6. It calls `p.Send(callback(err))`, so the result comes back to `Update` as an ordinary message.

`err` in the callback can be one of three things (`exec.go:102-129`):

| What failed | Value of `err` |
|---|---|
| Releasing the terminal | That error. The child never runs. |
| The child (couldn't start, or exited non-zero) | The child's error. Restore is still attempted, but **its error is thrown away**. |
| Child succeeded, restore failed | The restore error |
| Nothing | `nil` |

So check the child error types first. Anything else is a terminal problem.

```go
package main

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"os/exec"

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
	editing bool
	status  string
}

func editorCmd(path string) tea.Cmd {
	editor := os.Getenv("VISUAL")
	if editor == "" {
		editor = os.Getenv("EDITOR")
	}
	if editor == "" {
		editor = "vi"
	}
	// $EDITOR may contain args ("code --wait"), so let the shell split it.
	c := exec.Command("sh", "-c", `exec $EDITOR "$1"`, "sh", path)
	c.Env = append(os.Environ(), "EDITOR="+editor)

	// The callback runs on the event loop; keep it cheap and just wrap the error.
	return tea.ExecProcess(c, func(err error) tea.Msg {
		return editorFinishedMsg{err: err}
	})
}

func loadFile(path string) tea.Cmd {
	return func() tea.Msg {
		b, err := os.ReadFile(path)
		return fileLoadedMsg{content: string(b), err: err}
	}
}

func (m model) Init() tea.Cmd { return loadFile(m.path) }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "ctrl+c":
			// Raw mode disables ISIG: Ctrl+C is a key, not SIGINT.
			return m, tea.Interrupt
		case "q":
			return m, tea.Quit
		case "e":
			if m.editing {
				return m, nil
			}
			m.editing = true
			m.status = "editing…"
			return m, editorCmd(m.path)
		}

	case editorFinishedMsg:
		m.editing = false
		var exitErr *exec.ExitError
		switch {
		case msg.err == nil:
			m.status = "saved"
			return m, loadFile(m.path)
		case errors.As(msg.err, &exitErr):
			// Editor ran but exited non-zero (e.g. :cq). Terminal was restored
			// (best effort); keep the old content.
			m.status = fmt.Sprintf("editor exited %d; changes discarded", exitErr.ExitCode())
		case errors.Is(msg.err, exec.ErrNotFound), errors.Is(msg.err, fs.ErrNotExist):
			m.status = "editor not found: " + msg.err.Error()
		default:
			// Release or restore failed: the terminal state is suspect.
			// Exiting lets Run's shutdown path do its best cleanup.
			m.status = "terminal error: " + msg.err.Error()
			return m, tea.Quit
		}

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
	return tea.NewView(fmt.Sprintf("%s\n\n%s\n\ne: edit • q: quit • ctrl+c: interrupt", m.content, m.status))
}

func main() {
	p := tea.NewProgram(model{path: "notes.txt"})
	_, err := p.Run()
	switch {
	case errors.Is(err, tea.ErrInterrupted):
		os.Exit(130) // conventional 128+SIGINT
	case err != nil:
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
```

**Keep using the model after the editor closes.** You do, but only through messages. The `m` that returned the exec command is finished. Your state changes happen when `editorFinishedMsg` arrives. Reading the file is a separate `Cmd` so the event loop isn't doing file I/O.

**`q` versus Ctrl+C:**
- **`q`** is a normal quit. `tea.Quit` makes `Run` return `nil`, so the exit code is 0.
- **Ctrl+C in your TUI.** In raw mode the terminal doesn't turn it into SIGINT. You get a `KeyPressMsg` with the value `"ctrl+c"`. If you don't handle it, nothing happens. Return `tea.Interrupt`. The event loop catches `InterruptMsg` before it reaches `Update` and makes `Run` return `tea.ErrInterrupted` (`tea.go:792`). Exit with 130 so shells and scripts see it as an interrupt, not a clean quit. The terminal is restored on both paths.
- **Ctrl+C inside the editor.** `ignoreSignals` is 1 while the child runs. Any SIGINT that reaches the shared process group goes to the editor (vim and similar editors handle it themselves), and your program ignores it. After restore, Ctrl+C is a key again.
- **External `kill -INT`** while the TUI is active, not editing, still becomes `InterruptMsg`, giving the same `ErrInterrupted` and exit 130.

Only call `Program.ReleaseTerminal`/`RestoreTerminal` yourself from outside the event loop, such as a goroutine in `main`. Never call them from `Update`, and don't keep a `*tea.Program` in the model for this.
