**Give onboarding a linear screen-reader mode, using Huh’s `WithAccessible(true)`, and run it outside the full-screen Bubble Tea program.** This follows the tui-design skill’s Go and accessibility guidance.

NVDA reads terminal text changes. Full-screen redraws, moving highlights, and spinner frames can produce repeated or confusing speech; the visual layout supplies no navigable form semantics. Bubble Tea and Bubbles have no screen-reader mode of their own.

Huh v2 already provides the useful prompt behavior:

- `Select`: numbered choices; users type a number.
- `MultiSelect`: toggle numbered choices, then type `0` to finish.
- `Confirm`: `y`/`n`.
- Validation failures: printed errors followed by another prompt.

The critical integration change is **branching before `tea.NewProgram(...).Run()`**. Setting accessible mode on a form that remains embedded in the parent’s `Update`/`View` loop does not establish this separate, linear workflow.

```go
// Application helpers below are illustrative.
// Both paths share the same fields, validators, and result structure.
func runOnboarding(accessible bool) error {
    answers := OnboardingAnswers{}
    form := newOnboardingForm(&answers)

    if accessible {
        // No outer Bubble Tea program is running here.
        if err := form.WithAccessible(true).Run(); err != nil {
            return err
        }
        return finishOnboardingPlain(answers)
    }

    return runOnboardingTUI(form, &answers)
}
```

Expose `mycli onboard --accessible` or `--no-tui`, plus an app-specific environment variable and a persistent setting. Make it discoverable in ordinary command help, before users enter the TUI. Huh automatically enables accessible mode only for `TERM=dumb`; NVDA users commonly have another terminal type. `ACCESSIBLE` in Huh’s README is an example the application reads, not universal automatic detection.

Carry the linear contract through the whole flow:

- Keep output in scrollback; append status lines instead of repainting.
- Use descriptive labels, explicit defaults, and words such as “required.” Give errors a concrete correction.
- Remove decorative borders, repeated selection markers, column-dependent meaning, and animated progress. Print “Saving…” followed by a clear completion or failure message.
- Route prompts/progress/errors to stderr and results to stdout; configure and verify Huh’s output accordingly.
- Give each prompt an unattended equivalent through flags, config, or suitable input. With redirected output, select plain output; without interactive input, require supplied values rather than hanging.
- Continue into a linear app workflow after onboarding when accessibility mode is selected.

If onboarding is already open, let the parent program finish and restore the terminal before running plain prompts. Do not call `form.Run()` inside `Update` or let it compete with the active program for stdin.

**Validate with NVDA on Windows in the terminals your users actually use.** Have users complete onboarding, correct invalid input, choose multiple options, cancel, and hear the final outcome without sighted assistance. Check scrollback and terminal restoration afterward. Automated transcript tests can verify prompts and retries, but cannot establish usable speech behavior.

At 80×24 and 60 columns, the linear path should wrap naturally with no hidden fields or width gate. For the visual path, use a single-column form and collapse decorative chrome first. Exact clutter counts require a rendered frame; the accessible path should have no decorative border nesting.