Don't use that plan. Return `tea.ExecProcess` from `Update` and let Bubble Tea handle the handoff. Your version has three problems:

1. **`exec.Command(...).Run()` inside `Update` blocks the event loop.** Until the editor exits, no messages are processed. It also means `Update` stops being a pure state transition that you can unit-test.
2. **`defer p.RestoreTerminal()` doesn't do what it seems to.** It doesn't restore the user's shell. It's the second half of `ReleaseTerminal` and turns Bubble Tea's raw mode, alt screen and input modes back on. Final cleanup already happens in `Program.Run()` on normal exit, error and recovered panic.
3. **Keeping the old model after the editor exits shows stale data.** The editor probably changed the file, and repainting only redraws what the model already holds. You have to reload from disk.

## The lifecycle

```
Update ──"e"──▶ return tea.ExecProcess(cmd, cb)
                 │  Bubble Tea pauses input, leaves raw mode and the alt screen,
                 │  connects the editor to stdin/stdout/stderr, and waits
                 ▼
             editor runs (the terminal is the editor's)
                 │  editor exits → Bubble Tea turns its modes back on and repaints
                 ▼
             cb(err) → editorFinishedMsg{err} ──▶ Update
                 │  err is the editor's error, or a restore error if the editor
                 │  succeeded. If both failed, you get the editor's error.
                 ▼
             return loadFile(path)  ──▶ fileLoadedMsg ──▶ Update (new model)
```

```go
type editorFinishedMsg struct{ err error }
type fileLoadedMsg struct {
	content string
	err     error
}

func openEditor(path string) tea.Cmd {
	editor := os.Getenv("VISUAL")
	if editor == "" {
		editor = os.Getenv("EDITOR")
	}
	if editor == "" {
		editor = "vi"
	}
	parts := strings.Fields(editor) // handles EDITOR="code --wait"
	c := exec.Command(parts[0], append(parts[1:], path)...)
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

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "e":
			return m, openEditor(m.path)
		case "q":
			return m, tea.Quit // intentional quit: Run returns nil, exit 0
		case "ctrl+c":
			return m, tea.Interrupt // Run returns tea.ErrInterrupted
		}

	case editorFinishedMsg:
		var exitErr *exec.ExitError
		switch {
		case msg.err == nil:
			m.status = ""
		case errors.As(msg.err, &exitErr):
			// The editor exited non-zero (for example, vim :cq). Treat it as an abort.
			m.status = fmt.Sprintf("editor exited %d; changes may not be saved", exitErr.ExitCode())
		case errors.Is(msg.err, exec.ErrNotFound):
			m.status = "editor not found: set $VISUAL or $EDITOR"
			return m, nil // nothing ran, so there's nothing to reload
		default:
			// Either the editor failed to start or Bubble Tea couldn't restore the
			// terminal. Show it. Don't panic, don't call os.Exit.
			m.status = "editor: " + msg.err.Error()
		}
		// The file on disk is the source of truth. Reload it even after an
		// abort, because the editor may have saved before exiting non-zero.
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
```

All failures come back to `Update` as an ordinary message. You never handle an error halfway through the handoff, and the terminal is never left half-restored while your code is deciding what to do.

## `q` versus Ctrl+C

In raw mode, Ctrl+C doesn't send SIGINT. It arrives as a `tea.KeyPressMsg` like any other key, so choosing what it means is up to you:

| Key | Return | `p.Run()` returns | Exit code |
|---|---|---|---|
| `q` | `tea.Quit` | `nil` | 0: the user chose to quit |
| Ctrl+C | `tea.Interrupt` | `tea.ErrInterrupted` | 130: the shell convention for "interrupted" |
| External SIGINT/SIGTERM | (Bubble Tea's default handler) | managed shutdown | — |

In every case, terminal cleanup happens inside `Run()`. Map the result to an exit code in `main`, never in `Update`:

```go
func main() {
	p := tea.NewProgram(newModel(os.Args[1]))
	if _, err := p.Run(); err != nil {
		if errors.Is(err, tea.ErrInterrupted) {
			os.Exit(130)
		}
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
```

While the editor is running, Ctrl+C belongs to the editor. That's why the handoff exists: the editor's own keymap applies until it exits.

## If you really need `ReleaseTerminal`

This is only for handing the terminal to something that isn't a child process (an `*exec.Cmd`). In that case:

- Call the pair from a `tea.Cmd`, not from `Update`.
- Call `RestoreTerminal` explicitly right after the work finishes. Don't `defer` it as a safety net.
- Send the result back as a message.
- Reload any changed data in the handler, just as above.

For `$EDITOR`, use `ExecProcess`.

## Tests

- **Unit:** send `tea.KeyPressMsg{Code: 'c', Mod: tea.ModCtrl}` to `Update`, run the returned `Cmd`, and check that you get the interrupt message. `q` should give `tea.QuitMsg`. Send `editorFinishedMsg{err: &exec.ExitError{...}}` and `editorFinishedMsg{err: exec.ErrNotFound}` and check the status text and whether a reload `Cmd` came back.
- **PTY smoke test:** one run with `EDITOR=true` and one with `EDITOR=false`. Confirm the screen repaints and keys work afterward.
