The plan has four problems:

- **It blocks the event loop.** Running `exec.Command` inside `Update` stops Bubble Tea while the editor is open.
- **`Update` needs the `*Program`.** Your model would have to hold a reference to it, which it shouldn't.
- **The `defer` hides errors.** A deferred `RestoreTerminal()` throws away its error, so a failed restore never reaches `Update`.
- **The model is stale afterwards.** Restoring and repainting the terminal only redraws the model you already have. It doesn't pick up what the editor changed.

`Release`/`RestoreTerminal` is a low-level escape hatch. It's not a cleanup guard, and it isn't meant for this case. Use `tea.ExecProcess` instead. It runs the whole handoff for you:

1. Pause the program and release the terminal.
2. Connect the editor to the terminal's input and output.
3. Wait for the editor to exit.
4. Re-enter raw mode and the alternate screen, then repaint.
5. Send the result back to `Update` as a message.

## The lifecycle

```go
package main

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"strings"

	tea "charm.land/bubbletea/v2"
)

type editorFinishedMsg struct{ err error }
type fileLoadedMsg struct {
	body []byte
	err  error
}

type model struct {
	path   string
	body   []byte
	status string
	fatal  error // set when the terminal can't be trusted; reported after Run returns
}

func openEditor(path string) tea.Cmd {
	editor := os.Getenv("VISUAL")
	if editor == "" {
		editor = os.Getenv("EDITOR")
	}
	if editor == "" {
		editor = "vi"
	}
	args := strings.Fields(editor) // allows EDITOR="code --wait"
	c := exec.Command(args[0], append(args[1:], path)...)
	// ExecProcess releases the terminal, runs c, waits, restores and repaints,
	// then delivers this message to Update.
	return tea.ExecProcess(c, func(err error) tea.Msg { return editorFinishedMsg{err} })
}

func loadFile(path string) tea.Cmd {
	return func() tea.Msg {
		b, err := os.ReadFile(path)
		return fileLoadedMsg{b, err}
	}
}

func (m model) Init() tea.Cmd { return loadFile(m.path) }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "q":
			return m, tea.Quit // intentional quit: Run returns nil, exit 0
		case "ctrl+c":
			return m, tea.Interrupt // Run returns tea.ErrInterrupted
		case "e":
			m.status = "editing…"
			return m, openEditor(m.path)
		}

	case editorFinishedMsg:
		var exitErr *exec.ExitError
		var pathErr *fs.PathError
		switch {
		case msg.err == nil:
			m.status = "saved"
			return m, loadFile(m.path) // repaint alone shows stale data
		case errors.As(msg.err, &exitErr):
			// Editor ran and exited non-zero (e.g. vim :cq). The file may still have changed.
			m.status = fmt.Sprintf("editor exited %d", exitErr.ExitCode())
			return m, loadFile(m.path)
		case errors.Is(msg.err, exec.ErrNotFound), errors.As(msg.err, &pathErr):
			// Editor never started; nothing changed on disk.
			m.status = "cannot start editor: " + msg.err.Error()
			return m, nil
		default:
			// Child succeeded but restoration failed: the terminal isn't trustworthy.
			// Quit and let Run's final cleanup and main report it.
			m.fatal = fmt.Errorf("restoring terminal after editor: %w", msg.err)
			return m, tea.Quit
		}

	case fileLoadedMsg:
		if msg.err != nil {
			m.status = "reload failed: " + msg.err.Error()
			return m, nil
		}
		m.body = msg.body
	}
	return m, nil
}

func (m model) View() tea.View {
	v := tea.NewView(fmt.Sprintf("%s\n\n%s\ne edit · q quit", m.body, m.status))
	v.AltScreen = true
	return v
}

func main() {
	final, err := tea.NewProgram(model{path: os.Args[1]}).Run()
	switch {
	case errors.Is(err, tea.ErrInterrupted):
		os.Exit(130) // conventional 128+SIGINT
	case err != nil:
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if m, ok := final.(model); ok && m.fatal != nil {
		fmt.Fprintln(os.Stderr, m.fatal) // printed after Run restored the shell's terminal
		os.Exit(1)
	}
}
```

## How failures get back to `Update`

All failures arrive in one callback message, `editorFinishedMsg`:

- **The editor fails** (couldn't start, or exited non-zero): you get the child's error.
- **The editor succeeds but restoring the terminal fails:** you get the restore error.
- **Both fail:** you only get the child's error. A broken terminal can hide behind a non-zero exit. If that matters, add a key that forces a redraw, so users can recover from a garbled screen.

Bubble Tea doesn't give the restore error its own type, so the code above sorts errors cautiously. A non-zero exit or "editor not found" just updates the status line. Any other error is treated as an untrustworthy terminal: the app quits and reports it after `Run` has restored the shell's terminal. Don't print anything to the screen while the TUI owns it.

In every case where the editor actually ran, reload the file in a command (`loadFile`). Don't read it inside `Update`.

## `q` versus Ctrl+C

| | Key | Returned command | `Run()` result | Exit code |
|---|---|---|---|---|
| Intentional quit | `q` | `tea.Quit` | `(model, nil)` | 0 |
| Interrupt | Ctrl+C | `tea.Interrupt` | `tea.ErrInterrupted` | 130 |

- **Ctrl+C is an ordinary key while the app runs.** In raw mode it arrives as a `tea.KeyPressMsg`, not a signal, so you choose what it means. `tea.Interrupt` lets scripts and callers tell a cancel apart from a clean quit.
- **Don't call `os.Exit` inside `Update`.** It skips Bubble Tea's terminal restoration. Decide the exit code in `main`, after `Run` returns.
- **Bubble Tea handles signals sent from outside.** A SIGINT or SIGTERM from another process (not the keyboard) is turned into a normal managed shutdown, so don't add your own `signal.Notify`.
- **While the editor is open, it gets the keys.** Bubble Tea has stopped reading input, so `q` and Ctrl+C reach vim, not your `Update`. You don't need to guard against `e` being pressed twice.
- **If the screen has a text field, `q` should type a "q".** Only treat `q` as quit when no text input has focus. Ctrl+C should quit or cancel everywhere.

## Testing

You can test the `editorFinishedMsg` handling without launching an editor. Call `Update` directly with these messages and check the result:

- `nil` → a reload command
- an `*exec.ExitError` → a status message plus a reload
- `exec.ErrNotFound` → a status message and no command
- any other error → `fatal` is set and the command is `tea.Quit`

To check that the real handoff works with an actual editor, add one end-to-end test that runs the app in a real terminal session, using `EDITOR=true` or a script that changes the file.
