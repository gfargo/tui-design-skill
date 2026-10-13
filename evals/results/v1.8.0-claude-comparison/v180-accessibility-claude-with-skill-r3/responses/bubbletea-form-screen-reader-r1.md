The form is unusable with NVDA because it runs inside the full-screen app, and no styling change fixes that. NVDA works out what's new in a terminal by comparing the screen before and after each redraw. A full-screen form repaints all the time, so every arrow-key move re-reads the menu, the hidden cursor gives NVDA no focus to follow, and borders are read out as symbols. The fix is to run onboarding through Huh's accessible mode, outside the Bubble Tea program, behind a switch users turn on once.

## 1. Use Huh's accessible mode, run on its own

`form.WithAccessible(true)` drops the full-screen UI and asks each field as a plain line-by-line prompt:
- **Select:** a numbered list; the user types the number.
- **MultiSelect:** numbers toggled one at a time, with `0` to finish.
- **Confirm:** `y`/`n`.
- **Validation errors:** printed, then the prompt repeats.

All of it is appended text, which NVDA reads well.

One catch: this only works when Huh runs the form itself (`form.Run()`). If your parent model forwards messages to `m.form.Update` and draws `m.form.View()`, Bubble Tea is still drawing the screen and the flag does nothing. So build the form in one place and give it two ways to run:

```go
func newOnboardingForm(a *Answers) *huh.Form {
    return huh.NewForm(
        huh.NewGroup(
            huh.NewInput().Title("Project name").Value(&a.Name).
                Validate(func(s string) error {
                    if s == "" { return errors.New("Project name is required. Type a name and press Enter.") }
                    return nil
                }),
            huh.NewSelect[string]().Title("Region").
                Options(huh.NewOptions("us-east", "eu-west", "ap-south")...).
                Value(&a.Region),
            huh.NewConfirm().Title("Send anonymous usage data?").Value(&a.Telemetry),
        ),
    )
}

func main() {
    cfg := loadConfig()
    var a Answers

    if cfg.Accessible {
        if err := newOnboardingForm(&a).WithAccessible(true).Run(); err != nil {
            fmt.Fprintln(os.Stderr, "error: setup cancelled:", err)
            os.Exit(1)
        }
        saveAnswers(a)
        fmt.Fprintln(os.Stderr, "Setup complete. Saved settings for", a.Name+".")
        runPlain(cfg) // linear mode, see step 3
        return
    }

    // Existing path, unchanged: embedded form inside the full-screen program.
    p := tea.NewProgram(newModel(newOnboardingForm(&a)))
    if _, err := p.Run(); err != nil { /* ... */ }
}
```

The full-screen path stays as it is. Both paths share the same fields, titles and validation, so they can't drift apart.

**If onboarding has to run in the middle of a session** (for example, re-running setup from inside the app), don't embed it. Hand the terminal off with `tea.Exec`: write a small type with `Run()` and `SetStdin`/`SetStdout`/`SetStderr` methods whose `Run` calls the accessible form. Bubble Tea then leaves the alternate screen, runs the prompts in normal scrollback, and redraws when they finish. Re-read the saved answers in the callback; redrawing alone won't pick them up.

## 2. Give users a switch they set once

Don't try to detect a screen reader; there's no reliable way to do it. Huh only turns accessible mode on by itself for `TERM=dumb`, which NVDA users won't have. Offer three ways in, all feeding `cfg.Accessible`:

- a flag: `--accessible`
- an environment variable: `YOURAPP_ACCESSIBLE=1` (Huh's README uses `ACCESSIBLE`, so you could honor that too)
- a saved setting: `yourapp config set accessible true`, so it survives upgrades and new shells

gh does the same with `GH_ACCESSIBLE_PROMPTER` plus a matching config key. Mention the setting in `--help` and in the first line of output. The people who need it can't find it by looking at the screen.

Also give every onboarding question a flag (`--name`, `--region`, `--no-telemetry`) so setup can run with no prompts at all. Some screen-reader users will prefer that to any interactive form.

## 3. The rest of the app needs a linear mode too

Fixing onboarding alone just moves the problem to the next screen. Bubble Tea and Bubbles have nothing built in for screen readers, so `runPlain` is yours to write. It needs to:

- **Add new lines instead of repainting.** Report changes as new lines (`Saved config.yaml`) and stay in normal scrollback.
- **Use words for progress and status.** Replace spinners with an occasional line (`Uploaded 3 of 10`), and end each action with a status line.
- **Flatten tables.** Print each row as `Header: value` lines, or offer `--format json|csv`. Drop box drawing.
- **Number the choices.** Use Huh's accessible Select for any menu.
- **Label each line.** Start lines with `error:` or `warning:`, and have errors say what to do next.
- **Cover every action.** Nothing should be available only in the full-screen UI. Put results on stdout and prompts and progress on stderr.

## 4. Fix the wording inside the form

Accessible mode reads your titles, descriptions and errors exactly as written:
- Remove emoji, arrows and decorative Unicode from titles, descriptions and `NewNote` text.
- Write validation errors as instructions: "Project name is required. Type a name and press Enter." rather than `invalid: ^[a-z]+$`.
- Make each title make sense on its own, without the screen layout around it.

## 5. Verify with the people who reported it

- Write a unit test for the switch: flag, environment variable and config each turn on `cfg.Accessible`.
- Test by hand in Windows Terminal with NVDA (on Windows, since that's where NVDA runs). Go through setup without looking at the screen, including entering a wrong answer and cancelling.
- Then send a build to the users who reported this. Their feedback on the wording and on the linear mode will matter more than any automated check.

In short: build the form once, run it with Huh's accessible mode outside Bubble Tea when the user has opted in, and give the rest of the app a matching linear mode.
