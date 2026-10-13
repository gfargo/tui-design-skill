**The fix:** `WithTheme` now takes a `huh.Theme` interface. Built-in themes like `ThemeCharm` are plain functions with the signature `func(isDark bool) *Styles`. Wrap the function in `huh.ThemeFunc` and don't call it yourself:

```go
form := huh.NewForm(...).WithTheme(huh.ThemeFunc(huh.ThemeCharm))
```

From `charm.land/huh/v2@v2.0.3/theme.go:10-20`:

```go
type Theme interface {
	Theme(isDark bool) *Styles
}
type ThemeFunc func(isDark bool) *Styles
```

`huh.ThemeCharm(true)` returns a `*Styles`, and `*Styles` doesn't implement `Theme`, so it won't compile. The upgrade guide shipped with the module (`UPGRADE_GUIDE_V2.md:69-72`) shows exactly that call, so the guide is wrong on this point. If you really want a fixed variant, use a closure: `huh.ThemeFunc(func(bool) *huh.Styles { return huh.ThemeCharm(true) })`.

**How it learns the background is dark:** the form, each group and each field stores a `hasDarkBg` flag. That flag only changes when a `tea.BackgroundColorMsg` arrives (`form.go:537-538`, `group.go:281-282`, `field_input.go:280-281`, etc.). When the form renders, it calls `theme.Theme(f.hasDarkBg)` (`form.go:642-646`), so the styles are chosen on every render and update once the message comes in.

**Watch out:** nothing in Huh v2.0.3 actually asks the terminal for its background color.
- `Form.Init()` (`form.go:509-524`) only requests the window size.
- `Form.Run()` wraps the form in `compat.ViewModel`, which doesn't add a request either.
- Bubble Tea v2 only queries the terminal when a model returns `tea.RequestBackgroundColor` (`bubbletea/v2@v2.1.0/tea.go:846-847`).
- `hasDarkBg` starts as `false`.

As a result, **a form run with `form.Run()` always uses the light variant**, even on a dark terminal. The spinner package is the exception: it requests the color itself (`spinner/spinner.go:182`).

What to do depends on how you run the form:

- **Form embedded in your own Bubble Tea model:** request the color yourself and pass the reply on to the form:
  ```go
  func (m model) Init() tea.Cmd {
      return tea.Batch(m.form.Init(), tea.RequestBackgroundColor)
  }
  // In Update, keep forwarding every msg to m.form.Update(msg),
  // and BackgroundColorMsg will reach it.
  ```
- **Standalone `form.Run()`:** the form can't receive the message, so detect the background up front and lock in the variant:
  ```go
  isDark := lipgloss.HasDarkBackground(os.Stdin, os.Stderr) // huh renders to stderr by default
  form.WithTheme(huh.ThemeFunc(func(bool) *huh.Styles { return huh.ThemeCharm(isDark) }))
  ```
  The spinner detects the background the same way (`spinner.go:266-268`), and starts from `true` (dark) if detection isn't possible.
