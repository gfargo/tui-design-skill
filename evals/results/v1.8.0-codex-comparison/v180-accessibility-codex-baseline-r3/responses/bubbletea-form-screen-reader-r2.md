Provide a **plain, sequential onboarding mode outside the Bubble Tea program**. Removing the full-screen display alone won’t make a continuously redrawn form usable with NVDA.

Huh has an accessible mode:

```go
form := huh.NewForm(
    huh.NewGroup(
        huh.NewInput().
            Title("Your name").
            Value(&name),
        huh.NewConfirm().
            Title("Enable notifications?").
            Value(&notifications),
    ),
).WithAccessible(true)

if err := form.Run(); err != nil {
    return err
}
```

The crucial detail is **how you run it**: Huh’s accessible prompt flow is invoked through `form.Run()`. Setting `WithAccessible(true)` on a form that you continue to embed and drive through Bubble Tea’s `Init`, `Update`, and `View` is not sufficient.

For your app:

1. Add an explicit `--accessible` or `--plain` flag, and persist the preference. Document it in ordinary `--help` output so users can discover it before entering the TUI. Don’t depend on detecting NVDA.
2. When that mode is selected, run onboarding with `WithAccessible(true).Run()` **before starting Bubble Tea**. Bubble Tea must not simultaneously own stdin or leave the terminal in raw mode.
3. If onboarding can be opened from an already-running app, leave or suspend the TUI and restore the terminal before running the accessible prompts. Resume afterward. Running the form in a goroutine while Bubble Tea continues reading input is unsafe.
4. Keep the accessible path usable for subsequent settings and other essential actions, too. Accessible onboarding won’t help if the next screen is an inaccessible full-screen interface.

Use clear question titles, explicit defaults, and validation messages that explain how to fix the answer. Avoid relying on color, icons, cursor position, or changing text in place to communicate state. Disabling the alternate screen helps preserve terminal history, but **doesn’t address redraws or input handling by itself**.

Validate the actual experience with **NVDA on Windows in the terminal your users use**. Check that users can hear every question and option, enter answers, understand validation errors, cancel, and hear completion without sighted assistance. Include password input if your form uses it, and ensure secrets are never echoed.

I couldn’t retrieve the current upstream sources in this environment, so confirm the API against your pinned Huh v2 release. The key architectural change is to run its accessible prompt flow with exclusive control of a restored terminal, rather than inside the full-screen renderer.