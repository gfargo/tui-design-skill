In Huh v2, themes are no longer prebuilt `*Styles` values. A theme is now something that produces styles once the form knows whether the background is dark. `huh.ThemeCharm` is a function with the signature `func(isDark bool) *huh.Styles`, and you wrap it in `huh.ThemeFunc` so it fits the `Theme` interface:

```go
import "charm.land/huh/v2"

form := huh.NewForm(/* groups */).
    WithTheme(huh.ThemeFunc(huh.ThemeCharm))
```

Pass the function itself; don't call it. Writing `huh.ThemeCharm(true)` was the v1 approach of choosing light or dark yourself, and that's exactly what v2 removed.

**How the form detects a dark background**

Huh v2 uses Bubble Tea v2's background-color query:

1. When the form starts (`Init`), it asks the terminal for its background color with `tea.RequestBackgroundColor`.
2. The terminal replies, and Bubble Tea delivers a `tea.BackgroundColorMsg`.
3. The form's `Update` handles that message, calls `msg.IsDark()`, and runs your theme function with the result to rebuild its styles.

Until the reply arrives, the form uses a default. If the terminal never answers (some multiplexers and older terminals don't), it keeps that default.

**What this means for your code**

- **If you call `form.Run()` on its own**, this all happens automatically.
- **If the form is embedded in your own Bubble Tea model**, you need to do two things:
  - Return the form's `Init()` command from your model's `Init()` so the query is actually sent, for example with `tea.Batch(m.form.Init(), ...)`.
  - Pass every message on to `m.form.Update(msg)`, including `tea.BackgroundColorMsg`. If your `Update` swallows that message, the form never learns whether the background is dark.
- **If you want to force one variant**, for example in tests, write your own `ThemeFunc` that ignores the argument:
  ```go
  huh.ThemeFunc(func(bool) *huh.Styles { return huh.ThemeCharm(true) })
  ```
- **For a custom theme**, write it with the same `func(isDark bool) *huh.Styles` signature. Inside it, choose colors with `lipgloss.LightDark(isDark)`, which replaces `lipgloss.AdaptiveColor` from v1.

I couldn't find the Huh source on this machine (no vendored copy or module cache), so this answer is from memory of the v2 API. If it still doesn't compile, run `go doc charm.land/huh/v2 ThemeFunc` and `go doc charm.land/huh/v2 ThemeCharm` to confirm the exact signatures for your version.
