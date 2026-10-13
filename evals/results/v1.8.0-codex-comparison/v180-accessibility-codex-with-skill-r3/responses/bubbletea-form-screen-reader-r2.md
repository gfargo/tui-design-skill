**Add an explicit screen-reader mode that runs onboarding as linear prompts outside the Bubble Tea program.** Huh already supports this with `WithAccessible(true)`.

NVDA receives terminal text updates, not semantic form controls. Full-screen redraws, moving highlights, and spinner frames can become repeated announcements; the spatial layout provides little usable structure.

The crucial detail: **setting accessible mode on an embedded form is insufficient.** Huh’s accessible prompt runner is reached through `form.Run()`. Forwarding Bubble Tea messages to `form.Update()` and rendering `form.View()` does not invoke that runner.

Choose the path before starting your full-screen app:

```go
import "charm.land/huh/v2"

func runOnboarding(accessible bool, answers *Answers) error {
    form := buildOnboardingForm(answers) // shared fields and validation

    if accessible {
        return form.WithAccessible(true).Run()
    }

    return runOnboardingTUI(form) // your existing Bubble Tea embedding
}
```

Here, `Answers`, `buildOnboardingForm`, and `runOnboardingTUI` represent your application code. Both paths should use the same validation and persistence logic.

For the accessible path:

- Huh `Select` prints numbered choices; users type a number.
- `MultiSelect` toggles numbered choices, with `0` to finish.
- `Confirm` accepts `y`/`n`.
- Validation errors print before the prompt repeats.

Expose a documented flag such as `--accessible`, plus an environment variable or persistent preference. **Do not rely on NVDA detection:** Huh automatically enables this mode only for `TERM=dumb`. `NO_COLOR` removes color; it does not provide accessibility.

Carry the linear mode through the rest of onboarding: append labelled status and error lines, retain scrollback, disable animation, and announce completion explicitly. Remove borders, decorative markers, logos, and repeated headers from this path. Route prompts and progress to stderr and results to stdout; verify your pinned Huh version’s stream configuration. Provide flag/config equivalents for unattended onboarding, and avoid prompting when stdin is redirected unless explicitly requested.

If onboarding currently starts midway through `Program.Run()`, finish that program and let its terminal cleanup complete before running accessible prompts. Do not run a second interactive input reader while Bubble Tea owns the terminal.

Verify with **NVDA on Windows in the terminals your users actually use**. Have users complete choices, invalid-input correction, conditional steps, confirmation, and cancellation. Check that announcements occur once, earlier instructions remain reviewable, secrets stay concealed, and the terminal is restored after cancellation or errors. At 80×24 and 60 columns, linear prompts should wrap naturally and use scrollback without a minimum-size gate.

Huh’s mode addresses the form. Any subsequent full-screen Bubble Tea workflow still needs equivalent linear commands so users can complete the whole task.