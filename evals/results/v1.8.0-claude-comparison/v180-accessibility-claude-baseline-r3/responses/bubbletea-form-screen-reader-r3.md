I didn't find any Go code in the working directory, so this is general guidance. Send me the onboarding code and I can make the changes.

## Why it fails

A full-screen Huh form is hard for a screen reader to use. It runs on the alternate screen, repaints regions in place and moves the cursor around. The selected option is shown only by color or a `>` glyph. NVDA reads text as it appears on the terminal. With constant redraws it either reads stale fragments or doesn't announce the focused item at all.

## The fix: Huh's accessible mode, run outside Bubble Tea

Huh has an accessible mode built in. It replaces the TUI with plain prompts, one per line. Selects become numbered lists ("Enter a number"), confirms become y/N, and validation errors print as plain text before the prompt repeats. A screen reader handles this well.

```go
form := huh.NewForm(/* your groups */).WithAccessible(accessible)
```

**There's a catch.** Accessible mode reads stdin and writes stdout directly. It can't work as a `tea.Model` embedded in your running Bubble Tea program, because the program holds the terminal in raw mode on the alt screen. You need to run it outside the program in one of two ways.

**Option A (simplest): run onboarding before starting the program**

```go
if needsOnboarding && accessible {
    if err := onboardingForm().WithAccessible(true).Run(); err != nil {
        return err
    }
}
p := tea.NewProgram(newModel())
```

**Option B: onboarding has to happen mid-app.** Hand the terminal over with `tea.Exec`. It leaves the alt screen, restores normal terminal mode, runs your command, then resumes the app:

```go
type formExec struct {
    form   *huh.Form
    stdin  io.Reader
    stdout io.Writer
}

func (f *formExec) Run() error            { return f.form.WithInput(f.stdin).WithOutput(f.stdout).Run() }
func (f *formExec) SetStdin(r io.Reader)  { f.stdin = r }
func (f *formExec) SetStdout(w io.Writer) { f.stdout = w }
func (f *formExec) SetStderr(io.Writer)   {}

// in Update:
if m.accessible {
    return m, tea.Exec(&formExec{form: onboardingForm().WithAccessible(true)},
        func(err error) tea.Msg { return onboardingDoneMsg{err: err} })
}
// otherwise embed the form as a tea.Model as you do today
```

Read the values back from the variables bound with `.Value(&x)` when you handle `onboardingDoneMsg`.

## How users turn it on

A program can't reliably tell from inside the terminal that a screen reader is running, so make accessible mode opt-in and easy to find:

- Accept an environment variable (`ACCESSIBLE=1` is what Huh's own examples use) and a `--accessible` flag.
- Save the choice in your config so users only set it once.
- Mention it near the top of `--help` and in your README. A blind user who launches the full-screen UI may never discover the option from inside it.

## Also worth doing

- **Make every onboarding field available as a flag** (e.g. `mycli init --name … --region …`). Many screen-reader users prefer a fully non-interactive path, and scripts benefit too.
- **Check the rest of the app.** If users land in a full-screen TUI after onboarding, they're stuck again. Respect the same accessible setting there: print plain output, skip the alt screen and spinners, and don't rely on color alone to convey meaning.
- **Check form features in accessible mode:** password fields, dynamic `TitleFunc`/`OptionsFunc`, hidden groups and long select lists. Accessible mode is simpler than the TUI, so confirm each one behaves the way you expect.
- **Test with NVDA itself.** NVDA runs on Windows only, so test in Windows Terminal and the classic console. Even better, ask one of the users who reported the problem to try a build.
