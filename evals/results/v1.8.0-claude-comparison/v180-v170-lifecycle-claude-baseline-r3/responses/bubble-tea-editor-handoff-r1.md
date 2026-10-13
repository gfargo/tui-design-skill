I checked the installed source (`charm.land/bubbletea/v2@v2.1.0`, `exec.go` and `tea.go`). Your plan has three problems, and `tea.ExecProcess` already handles all of them.

## Why the manual approach is wrong

1. **It blocks the event loop.** `Update` runs on the event loop. Running `exec.Command(...).Run()` inside it freezes message handling until the editor exits, outside the framework's control.
2. **The model has to hold a `*tea.Program`.** That links the model to the runtime, and your code then manages the terminal at the same time as the Program does.
3. **Errors get lost.** With `defer p.RestoreTerminal()`, the restore error is thrown away. The child's error never becomes a message either, so `Update` can't react to it. "Keep using the model" after the call is also risky: whatever you change after `Update` returns isn't the state the runtime has.

## What `ExecProcess` does (v2.1.0)

When the event loop receives the exec message, it runs `p.exec` synchronously (`tea.go:858`, marked "NB: this blocks"). That pauses the loop on purpose and in a controlled way:

```
releaseTerminal  ── fails ──► fn(releaseErr) sent; child never runs
      │ (sets ignoreSignals=1, cancels input reader, stops renderer, restores cooked mode)
child.Run()      ── fails ──► RestoreTerminal() attempted, its error DISCARDED; fn(childErr) sent
      │ ok
RestoreTerminal()             (ignoreSignals=0, raw mode, new reader, renderer, resize check)
      └────────► fn(restoreErr) sent  (nil on full success)
```

Your callback is called exactly once, with one of three errors: release, child, or restore. Note that if the child fails, a restore failure is hidden behind the child's error. Stdin and stdout are attached to the Program's terminal unless you set them yourself.

## Correct lifecycle

```go
package main

import (
	"errors"
	"os"
	"os/exec"
	"strings"

	tea "charm.land/bubbletea/v2"
)

type editorFinishedMsg struct {
	path string
	err  error
}

type model struct {
	path    string
	content string
	editing bool
	err     error
}

func openEditor(path string) tea.Cmd {
	editor := os.Getenv("EDITOR")
	if editor == "" {
		editor = "vi"
	}
	// $EDITOR may carry args, e.g. "code -w".
	parts := strings.Fields(editor)
	c := exec.Command(parts[0], append(parts[1:], path)...)

	return tea.ExecProcess(c, func(err error) tea.Msg {
		return editorFinishedMsg{path: path, err: err}
	})
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "ctrl+c":
			// Raw mode: ^C arrives as a key, not SIGINT. Always honor it.
			return m, tea.Interrupt // Run returns tea.ErrInterrupted
		case "q":
			// Normal quit, but only when 'q' isn't text input.
			if m.editing {
				break
			}
			return m, tea.Quit // Run returns nil error
		case "e":
			m.editing = true // state recorded before the editor launches
			return m, openEditor(m.path)
		}

	case editorFinishedMsg:
		m.editing = false
		if msg.err != nil {
			var exitErr *exec.ExitError
			if errors.As(msg.err, &exitErr) {
				// Editor exited non-zero (e.g. :cq). Treat as "cancelled".
				m.err = msg.err
				return m, nil
			}
			// Could not start editor, or terminal release/restore failed.
			// If restore failed the TUI may be unusable: bail out cleanly.
			m.err = msg.err
			return m, tea.Quit
		}
		// Success: re-read the file. That's the editor's actual output.
		b, err := os.ReadFile(msg.path)
		if err != nil {
			m.err = err
			return m, nil
		}
		m.content, m.err = string(b), nil
	}
	return m, nil
}

func (m model) View() tea.View {
	s := m.content + "\n\n[e] edit  [q] quit  [ctrl+c] abort"
	if m.err != nil {
		s += "\nerror: " + m.err.Error()
	}
	return tea.NewView(s)
}

func main() {
	_, err := tea.NewProgram(model{path: "notes.txt"}).Run()
	if errors.Is(err, tea.ErrInterrupted) {
		os.Exit(130) // conventional 128+SIGINT
	}
	if err != nil {
		os.Exit(1)
	}
}
```

Key points:
- **`Update` returns a `tea.Cmd`. It never touches the terminal.** All state changes happen in `Update`: before the editor launches (`editing = true`) and when the result arrives as `editorFinishedMsg`. Nothing changes the model while the editor is running.
- **The result always comes back as a message.** A start failure, non-zero exit, or release/restore failure all arrive as `editorFinishedMsg.err`. Decide in `Update`: a non-zero exit is a cancellation, but a restore failure probably means you should quit.

## `q` vs Ctrl+C

- **`q`** is an app-level shortcut. Ignore it when a text input has focus. Return `tea.Quit`, and `Run` returns `nil`.
- **Ctrl+C in raw mode** doesn't raise SIGINT. The TTY passes it through as a byte, and you receive `KeyPressMsg` `"ctrl+c"`. If you don't handle it, Ctrl+C does nothing. Always handle it no matter which input has focus. Return `tea.Interrupt` so `Run` returns `tea.ErrInterrupted` and you can exit with 130. `tea.Quit` also works if you don't need to tell the two apart.
- **Real SIGINT/SIGTERM** (when input isn't a TTY, or from `kill`): Bubble Tea's signal handler converts these to `InterruptMsg` or `QuitMsg` itself (`tea.go:689-699`).
- **While the editor is running**, `ignoreSignals` is 1, so a SIGINT from a cooked-mode child's Ctrl+C reaches the child but doesn't kill your TUI. Most editors use raw mode, so Ctrl+C is just a keystroke to them. Either way, you only regain control when the child exits and the callback message arrives.
