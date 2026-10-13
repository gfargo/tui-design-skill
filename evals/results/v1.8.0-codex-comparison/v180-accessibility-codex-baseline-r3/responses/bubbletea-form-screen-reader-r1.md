Give onboarding a **screen-reader mode that runs outside the full-screen Bubble Tea app**. Huh’s accessible mode uses sequential, ordinary terminal prompts, which are much easier for NVDA to follow than a screen that continually redraws.

The key change is architectural: **`WithAccessible(true)` needs Huh’s standalone `Run()` path.** Setting it on a form embedded in your app’s `Update`/`View` loop won’t turn that interface into accessible prompts.

Expose a flag such as `--accessible` and choose the path **before starting Bubble Tea**:

```go
import "charm.land/huh/v2"

func runOnboarding(accessible bool, name *string) error {
    form := huh.NewForm(
        huh.NewGroup(
            huh.NewInput().
                Title("Your name").
                Description("Enter the name to use for your account.").
                Value(name),
        ),
    )

    return form.WithAccessible(accessible).Run()
}
```

At your command entry point:

```go
if accessible {
    // Run before starting the Bubble Tea program.
    return runOnboarding(true, &config.Name)
}

// Start your usual Bubble Tea app with its embedded form.
return runFullScreenApp()
```

If onboarding starts after the app is already running, have the outer program exit and restore the terminal first, run the accessible form, then restart the app if needed. Don’t call the blocking `form.Run()` from `Update`, or run it concurrently with Bubble Tea: both would compete for terminal input and output.

For a usable end-to-end experience:

- Document `yourcli onboard --accessible` in ordinary `--help` output. Don’t require navigating the TUI to enable it.
- Keep accessible output sequential: clear labels, instructions, validation errors and completion messages; avoid screen clearing, cursor movement and animated spinners.
- Share field definitions and validation between both paths.
- Provide accessible follow-up commands or output too; returning users immediately to an inaccessible full-screen interface only fixes part of the workflow.
- Test with blind users using NVDA and their actual Windows terminal. Cover invalid input, choices, cancellation and secret entry without printing secrets.

Turning off the alternate screen alone won’t solve this: the normal renderer still updates terminal cells rather than presenting a readable sequence of prompts.

I couldn’t verify your exact Huh v2 revision here—the workspace contains no source files and upstream access was unavailable—so confirm the import and API against your pinned version. The important boundary is standalone accessible prompting versus embedded full-screen rendering.