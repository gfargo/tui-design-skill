**Give onboarding a linear screen-reader mode, and run it outside the enclosing Bubble Tea program.** Huh v2 already supplies the prompt runner you need:

```go
form.WithAccessible(true)
err := form.Run()
```

The crucial detail is **where you run it**. Accessible mode takes effect through Huh’s standalone `Run()` path. Adding `WithAccessible(true)` to a form that your parent still drives through `Update()` and `View()` does not turn that full-screen app into accessible prompts.

Choose the mode before starting the parent program. Conceptually:

```go
// Imports: charm.land/huh/v2 and charm.land/bubbletea/v2
form := buildOnboardingForm(&answers)

if accessible {
    // No enclosing Bubble Tea program owns the terminal here.
    if err := form.WithAccessible(true).Run(); err != nil {
        return err
    }
    return finishOnboardingPlain(answers)
}

_, err := tea.NewProgram(newAppModel(form)).Run()
return err
```

Both paths should use the same answers, validation, and save logic.

Full-screen redraws, moving highlights, and spinner frames can produce noisy or incomplete NVDA announcements. Terminal text also lacks the navigable form structure users expect from a GUI. Huh’s accessible mode instead presents sequential prompts: numbered choices for selects, individual number toggles with `0` to finish multi-selects, `y`/`n` confirmations, and printed validation errors before retrying.

Make that a complete product path:

- Expose `--accessible` or `--no-tui`, plus an environment variable and persistent setting. Document it in ordinary CLI help, before onboarding. Huh automatically enables accessible mode only for `TERM=dumb`; don’t rely on detecting NVDA.
- Keep the entire workflow linear, including authentication, progress, confirmation, errors, and completion. Bubble Tea and Bubbles have no equivalent accessibility mode for the surrounding app.
- Preserve scrollback; remove borders, decorative markers, aligned columns, and animations. Print explicit status lines such as `Setup complete` and actionable errors such as `error: Enter a project name.`
- Keep prompts and progress on stderr and results on stdout. Verify Huh’s stream configuration for your pinned version. When input is noninteractive, require documented configuration inputs instead of waiting for answers.

**Validate with NVDA in the Windows terminal your users actually use.** Exercise invalid input and retry, each choice type, cancellation, successful saving, and any conditional steps. Check that labels and instructions are announced, choices remain reviewable in scrollback, and completion is unmistakable. Unit tests can verify shared validation and persistence; they cannot establish whether NVDA speech is usable.

At 80×24 and 60 columns, the accessible path should remain one prompt at a time with wrapping text and no clipping. For the visual path, remove nested form borders and repeated decorative markers where present; actual clutter counts require seeing its rendered output.