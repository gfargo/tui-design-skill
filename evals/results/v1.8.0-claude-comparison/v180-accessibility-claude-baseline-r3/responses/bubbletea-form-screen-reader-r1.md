There's no Go code in this directory, so this answer is based on how Huh and Bubble Tea work, not on your code. Paste or point me at the onboarding model and I can make the change.

## Why NVDA can't use it

There are two problems, and both have to be fixed:

1. **Full-screen redrawing.** In a full-screen terminal app the screen is repainted constantly and the cursor jumps around. NVDA reads the console as a grid of characters, so users hear fragments, repeated text, or nothing. Arrow-key select lists are especially bad because the only sign of which item is chosen is a highlight or a `>` drawn somewhere on screen.
2. **Huh's accessible mode doesn't apply when the form is embedded.** Huh has `WithAccessible(true)`, which replaces the interactive form with plain prompts, one line at a time (for example "Choose a number 1–3", then the user types an answer and presses Enter). That mode only takes effect when the form runs on its own through `form.Run()` / `form.RunWithContext()`. If you embed the form as a `tea.Model` inside your own program, the setting is ignored and users still get the visual form.

## The fix

**1. Give users a way to opt in.** A terminal app can't reliably detect a screen reader, so add an explicit switch. Charm's examples use an `ACCESSIBLE` environment variable; add a `--accessible` flag as well, and ideally save the choice in your config.

```go
accessible := os.Getenv("ACCESSIBLE") != "" || cfg.Accessible || flagAccessible
```

**2. In accessible mode, run the form outside your Bubble Tea program.**

If onboarding happens before the main UI, the simplest option is to run it first:

```go
form := buildOnboardingForm(&answers).WithAccessible(accessible)

if accessible {
    if err := form.Run(); err != nil { // plain line-by-line prompts
        return err
    }
} else {
    // existing path: embed form in your tea.Model as today
}
// then start (or skip) the main tea.Program
```

If onboarding is triggered from inside the running app, use `tea.Exec`. It hands the terminal back (leaving full-screen mode and restoring normal input), runs your code, then resumes the app:

```go
type formCmd struct{ form *huh.Form }

func (c *formCmd) Run() error             { return c.form.Run() }
func (c *formCmd) SetStdin(io.Reader)     {}
func (c *formCmd) SetStdout(io.Writer)    {}
func (c *formCmd) SetStderr(io.Writer)    {}

// in Update:
return m, tea.Exec(&formCmd{form.WithAccessible(true)}, func(err error) tea.Msg {
    return onboardingDoneMsg{err}
})
```

**3. Keep the rest of the accessible path in plain text:**
- Don't switch to full-screen mode (in v2, leave `AltScreen` false on the `tea.View`). Ideally, skip the full-screen UI entirely in accessible mode and print results as normal text.
- Replace spinners and progress bars with plain status lines such as "Saving config… done."
- Don't rely on color or symbols alone to convey meaning. Write out error and validation messages, and give every field a clear `Title`, plus a `Description` where it helps. In accessible mode those titles become the spoken prompts.

## Before shipping

- Test with NVDA in both Windows Terminal and the classic Windows console window. They behave differently.
- Make the option easy to find: mention `--accessible` in `--help`, in the first line of output, and in your README.
- Ask the users who reported the problem to try a build, since they're your best test.
