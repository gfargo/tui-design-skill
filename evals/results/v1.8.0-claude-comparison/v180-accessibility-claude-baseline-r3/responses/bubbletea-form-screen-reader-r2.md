There's no Go code in this directory, so this is based on how Huh and Bubble Tea work, not on your code. If you point me at the repo, I can make the actual change.

## Why it breaks

A full-screen Bubble Tea app uses the alternate screen and redraws regions with cursor movement. NVDA reads the Windows console as a stream of text. It gets either nothing useful or a jumble of redrawn fragments. It has no idea which field has focus or which option is highlighted, because "highlighted" only means a color or a `>` character drawn somewhere on the grid.

## The fix: Huh's accessible mode, run outside Bubble Tea

Huh has an accessible mode for exactly this. It drops the TUI and asks plain, sequential prompts on stdin/stdout:
- Inputs are a simple "Title: " prompt.
- Selects become a numbered list where the user types a number.
- Confirms become y/N.
- Validation errors are printed as text.

Screen readers handle this well.

The catch: **accessible mode only takes effect when you call `form.Run()`**. If you embed the form as a `tea.Model` inside your full-screen program, it keeps rendering visually. So you need to get the form out of the Bubble Tea renderer.

### Option A: run onboarding before the program starts (simplest)

```go
accessible := *flagAccessible || os.Getenv("ACCESSIBLE") != "" || cfg.Accessible

if needsOnboarding(cfg) {
    var ans onboardingAnswers
    form := newOnboardingForm(&ans).WithAccessible(accessible)
    if err := form.Run(); err != nil {
        return err // includes huh.ErrUserAborted
    }
    cfg.Accessible = accessible // remember the choice
    saveConfig(cfg, ans)
}

p := tea.NewProgram(newModel(cfg))
```

### Option B: onboarding is launched from inside the running app

Hand the terminal over with `tea.Exec`. It suspends the renderer, leaves the alt screen, runs your command, then restores the app:

```go
type formExec struct{ form *huh.Form }

func (f *formExec) Run() error            { return f.form.Run() }
func (f *formExec) SetStdin(io.Reader)    {}
func (f *formExec) SetStdout(io.Writer)   {}
func (f *formExec) SetStderr(io.Writer)   {}

// in Update:
if m.accessible {
    return m, tea.Exec(&formExec{form: newOnboardingForm(&m.ans).WithAccessible(true)},
        func(err error) tea.Msg { return onboardingDoneMsg{err} })
}
// otherwise embed the form as a model like you do today
```

## Detecting who needs it

You can't reliably detect NVDA from a terminal program, so let users opt in and make that easy to discover:
- A `--accessible` flag, plus an env var. `ACCESSIBLE=1` is the convention in Huh's own examples.
- Mention the flag in `--help` and on the very first line of output, *before* anything goes full-screen. For example: "Using a screen reader? Re-run with --accessible."
- Save the choice to config so they only have to set it once.

## Other things worth doing

1. **Check your field text.** In accessible mode, the Title and Description are all the user gets. Placeholders, colors and inline hints aren't read. Make every Title self-explanatory, e.g. "Default region (e.g. us-east-1)", and put defaults in the text.
2. **Respect the flag in the rest of the app.** In Bubble Tea v2, alt screen is set per frame through `tea.View`'s `AltScreen` field. When accessible, leave it off, skip spinners and animations, and print status as plain lines.
3. **Offer a non-interactive path**, such as `mycli init --name foo --region us-east-1 --yes`. Many screen reader users prefer flags to any prompt.
4. **Test with the real thing.** Use NVDA in both Windows Terminal and conhost, since they behave differently. VoiceOver on macOS is a useful second check. Ideally, have one of the users who reported the problem try the build before you ship it.

The core change is small: about one line (`.WithAccessible(accessible)`) plus making sure the form runs through `form.Run()` and not inside your renderer. Most of the remaining work is making the opt-in easy to find and the prompt text clear.
