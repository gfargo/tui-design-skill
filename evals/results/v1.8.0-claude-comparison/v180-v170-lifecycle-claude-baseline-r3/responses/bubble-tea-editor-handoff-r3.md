Don't call `ReleaseTerminal`/`RestoreTerminal` from `Update`, and don't run the child there. Return a `tea.ExecProcess` command instead. Bubble Tea then releases the terminal, runs the child, restores the terminal, and sends a message you choose back to `Update`.

## Why your plan breaks

- **`Update` has to return quickly.** It runs on the event loop. Blocking it on `cmd.Run()` freezes rendering and message handling. You'd also be releasing the terminal while the renderer and input reader still think they own it.
- **`defer RestoreTerminal()` loses the error.** `Update` can't return an error, so a failed restore disappears and the app keeps running on a terminal in an unknown state.
- **Keeping a `*tea.Program` in the model is a code smell.** `Update` should only touch the model and return commands.
- **"Keep using the model" is fine, but only through messages.** The model is a value. Record what you're waiting for (`editing`, temp file path) and finish the work when the result message arrives.

## Correct lifecycle

```go
package main

import (
	"errors"
	"fmt"
	"os"
	"os/exec"

	tea "charm.land/bubbletea/v2"
)

type editorFinishedMsg struct {
	path string
	err  error // release, child, or restore failure
}

type model struct {
	text    string
	editing bool   // guards against double launch
	tmpPath string
	err     error
}

func openEditor(path string) tea.Cmd {
	editor := os.Getenv("EDITOR")
	if editor == "" {
		editor = "vi"
	}
	// $EDITOR may contain args ("code -w"), so let the shell split it.
	// Pass the path as $1 so it isn't re-parsed by the shell.
	c := exec.Command("sh", "-c", editor+` "$1"`, "sh", path)

	return tea.ExecProcess(c, func(err error) tea.Msg {
		return editorFinishedMsg{path: path, err: err}
	})
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "ctrl+c":
			// Raw mode: this is a key event, not SIGINT.
			return m, tea.Interrupt
		case "q":
			return m, tea.Quit
		case "e":
			if m.editing {
				return m, nil
			}
			f, err := os.CreateTemp("", "edit-*.txt")
			if err != nil {
				m.err = err
				return m, nil
			}
			_, werr := f.WriteString(m.text)
			cerr := f.Close()
			if err := errors.Join(werr, cerr); err != nil {
				os.Remove(f.Name())
				m.err = err
				return m, nil
			}
			m.editing, m.tmpPath, m.err = true, f.Name(), nil
			return m, openEditor(f.Name())
		}

	case editorFinishedMsg:
		m.editing = false
		defer os.Remove(msg.path)

		if msg.err != nil {
			var exitErr *exec.ExitError
			if errors.As(msg.err, &exitErr) {
				// Editor ran but exited non-zero (e.g. :cq, or killed by SIGINT).
				// Treat as "cancelled": keep the old text.
				m.err = fmt.Errorf("editor exited: %w", msg.err)
				return m, nil
			}
			// Couldn't start the editor, or couldn't release/restore the
			// terminal. If restore failed, the TTY is suspect, so don't keep running.
			m.err = msg.err
			return m, tea.Quit
		}

		b, err := os.ReadFile(msg.path)
		if err != nil {
			m.err = err
			return m, nil
		}
		m.text = string(b)
	}
	return m, nil
}

func (m model) Init() tea.Cmd { return nil }

func (m model) View() tea.View {
	s := m.text + "\n\n[e] edit  [q] quit\n"
	if m.err != nil {
		s += "error: " + m.err.Error() + "\n"
	}
	return tea.NewView(s)
}

func main() {
	_, err := tea.NewProgram(model{}).Run()
	switch {
	case errors.Is(err, tea.ErrInterrupted):
		os.Exit(130) // conventional exit code for Ctrl+C
	case err != nil:
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
```

## How failures get back to `Update`

The runtime's exec path does roughly this:

1. **Release the terminal.** It stops the input reader and renderer and restores the original tty mode. If this fails, the child never runs and your callback gets that error.
2. **Run the child** with the program's stdin/stdout. If the child fails (it can't start, or exits non-zero), the runtime still tries to restore the terminal, but that restore error is thrown away. Your callback gets the child's error.
3. **If the child succeeds,** the runtime restores the terminal (raw mode, input reader, full repaint) and your callback gets the restore error, or `nil`.

So you always get exactly one `editorFinishedMsg`, and `err` holds the first thing that went wrong. `*exec.ExitError` means the editor ran and the terminal came back. Any other error means something more basic failed. Bubble Tea's internals can change, so check the `exec` implementation in the version you're pinned to.

## `q` vs Ctrl+C

- **While the editor is running:** your program isn't reading input at all, so all keys go to the editor. Vim and similar editors run in raw mode and treat Ctrl+C as a normal key. If the child is in cooked mode, Ctrl+C sends SIGINT to the whole foreground process group, which includes your app. Bubble Tea ignores signals while the terminal is released, so only the child dies. You then get an `*exec.ExitError` and should treat it as "cancelled", not "quit the app".
- **Back in your TUI (raw mode):** Ctrl+C is not a signal. It arrives as `tea.KeyPressMsg` with `String() == "ctrl+c"`. If you don't handle it, nothing happens, because v2 doesn't quit on it automatically. Always handle it.
  - **`ctrl+c` → `tea.Interrupt`:** `Run` returns `tea.ErrInterrupted`, so you can exit with 130 and callers and scripts can tell it was an interrupt. Don't put a confirmation in front of Ctrl+C. It should always work as the escape hatch.
  - **`q` → `tea.Quit`:** a normal exit with code 0. This is where an "unsaved changes?" prompt belongs. Disable `q` while a text input is focused so typing the letter q doesn't quit the app.
- An external SIGINT/SIGTERM (e.g. `kill -INT`) is still caught by Bubble Tea, which restores the terminal on the way out. You don't need your own `signal.Notify` for this.

Two smaller notes:
- GUI editors need a wait flag (`code -w`, `subl -w`). Without it the child returns immediately and you'll read the file before the user has edited it.
- The `editing` flag stops a second `e` press that was already queued from launching a second editor.
