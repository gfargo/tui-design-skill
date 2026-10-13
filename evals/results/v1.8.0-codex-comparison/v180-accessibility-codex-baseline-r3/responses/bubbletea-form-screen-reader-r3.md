Give onboarding a **separate screen-reader mode that runs outside your full-screen Bubble Tea app**. Removing colors or improving keyboard navigation alone won’t make NVDA reliably interpret a terminal that continually redraws.

Huh provides an accessible mode:

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
)

if err := form.WithAccessible(true).Run(); err != nil {
    return err
}
```

The critical detail is **where you run it**. Accessible mode uses a different prompt flow; don’t embed it in your app’s `Init`/`Update`/`View` cycle and expect it to become accessible. Run it before starting Bubble Tea, or fully exit the running program, run the accessible form, then restart the app with the collected values. Bubble Tea must release terminal input and restore the terminal first.

For your CLI:

- Expose an explicit option such as `mycli onboard --accessible`, plus a persistent preference. Make it discoverable through ordinary `--help` output before users enter the TUI.
- Choose the mode before starting the full-screen app. Don’t depend on automatic NVDA detection; there’s no reliable cross-platform screen-reader detection.
- In accessible onboarding, keep prompts sequential and use clear labels, instructions, defaults, and validation errors. Avoid redraws, spinners, and information conveyed only through color.
- Offer flags or a configuration-file path for completing onboarding without interactive prompts, too.

**Test the complete flow with NVDA on Windows in the terminals your users actually use.** Check prompt announcements, input, validation and retry, selection, confirmation, cancellation, and terminal restoration. Test password entry separately so secrets aren’t accidentally echoed or repeated in summaries. Huh’s accessible option is a starting point, not proof that the whole flow works.

I couldn’t verify your exact Huh v2 release’s API here, and the workspace contains no Go source. Confirm `WithAccessible(true)` against your pinned version; the architectural fix remains running the accessible prompt flow independently of the full-screen renderer.