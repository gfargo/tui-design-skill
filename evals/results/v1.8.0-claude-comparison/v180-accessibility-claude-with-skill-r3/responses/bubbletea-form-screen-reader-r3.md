Huh's accessible mode is the fix, but it can't run inside your Bubble Tea program. You need to run the onboarding form before the program starts. Simply adding `WithAccessible(true)` to the embedded form won't work.

## Why NVDA fails today

NVDA finds new text in a terminal by comparing the screen before and after each change. Your full-screen form redraws the whole screen on every keypress. So each arrow press in a Select re-reads the menu, focus changes are announced as random new text, and borders and styling are read out as symbols. The terminal cursor, which screen readers follow, is usually hidden. Changing the theme or layout won't fix this.

## The fix: Huh's accessible mode, run before the program starts

`form.WithAccessible(true)` drops Bubble Tea and asks each field as a plain prompt, one line at a time:

- **Select:** a numbered list; the user types a number.
- **MultiSelect:** the user toggles numbers one at a time, then types `0` to finish.
- **Confirm:** `y`/`n`.
- **Validation errors** print as text, then the prompt repeats.

This is the mode gh uses (`GH_ACCESSIBLE_PROMPTER`).

Because accessible mode skips Bubble Tea, an embedded form's `Update`/`View` would bypass it. Build the form in one shared constructor and choose the path in `main`:

```go
func newOnboardingForm(a *Answers) *huh.Form {
    return huh.NewForm(
        huh.NewGroup(
            huh.NewInput().Title("Your name (required)").Value(&a.Name).
                Validate(requiredf("Name is required. Type your name and press Enter.")),
            huh.NewSelect[string]().Title("Default region").
                Options(huh.NewOptions("US East", "EU West", "Asia Pacific")...).
                Value(&a.Region),
        ),
    )
}

func main() {
    cfg := loadConfig()
    a11y := accessibleMode(cfg)

    if !cfg.Onboarded && a11y {
        var ans Answers
        err := newOnboardingForm(&ans).WithAccessible(true).Run()
        if errors.Is(err, huh.ErrUserAborted) {
            fmt.Fprintln(os.Stderr, "Setup cancelled. Nothing was saved.")
            os.Exit(130)
        }
        if err != nil { /* report in words, exit non-zero */ }
        cfg.apply(ans); cfg.Onboarded = true; saveConfig(cfg)
        fmt.Fprintln(os.Stderr, "Setup complete. Settings saved to", configPath())
    }

    if a11y {
        os.Exit(runPlain(cfg)) // see "The rest of the app" below
    }
    // Sighted path is unchanged: the full-screen program embeds the same form.
    p := tea.NewProgram(newModel(cfg))
    if _, err := p.Run(); err != nil { log.Fatal(err) }
}

func accessibleMode(cfg Config) bool {
    if v, ok := os.LookupEnv("MYAPP_ACCESSIBLE"); ok { return v != "" && v != "0" }
    if cfg.Accessible { return true }
    return os.Getenv("TERM") == "dumb"
}
```

A shared constructor keeps field labels and validation identical in both paths.

## How users turn it on

You can't reliably detect a screen reader, and neither can Ink, Gemini CLI or Claude Code. They all make users opt in, and so should you. Offer three ways that all set the same thing:

- an `--accessible` flag;
- a `MYAPP_ACCESSIBLE=1` environment variable;
- a saved `accessible: true` config key, so users set it once.

Mention it in `--help` and on the first line the app prints. A blind user has to be able to find it without first getting through the full-screen UI.

Also add a flag for every onboarding question (`myapp init --name … --region …`) so setup can run with no prompts at all. Many screen-reader users prefer that, and it also helps scripts and CI.

## Make the questions read well aloud

Once the questions are spoken in order, their wording matters more than it did on screen:

- **Titles make sense spoken alone.** Write "Default region", not "Region ▸". Put "(required)" in the title text. Huh's red `*` is its error marker, not a required-field marker, and screen readers either skip it or read it out.
- **Option labels are short, distinct words.** Remove emoji, arrows and symbols; they get read out in full.
- **Errors say what to do next**, e.g. "Name is required. Type your name and press Enter." A bare "invalid" doesn't help.
- **No ASCII-art Notes or banners.** If a `NewNote` is purely decorative, drop it when `a11y` is on.
- **Watch long MultiSelects.** Toggling one number at a time gets tedious past about 6 options. Consider splitting them into Confirms or a comma-separated Input.
- **End with a status line.** Without one, a successful finish is silent, and users can't tell whether setup worked.

## The rest of the app

Fixing onboarding only gets them past the first screen. Bubble Tea and Bubbles have no screen-reader support, so whatever comes after onboarding has the same problem. `runPlain` needs to be a real linear mode:

- New results are printed as new lines; nothing is redrawn in place.
- Progress is an occasional line like "Uploaded 3 of 10", not a spinner.
- Tables print as `Header: value` lines, or as `--format json|csv`.
- Menus are numbered; reuse Huh's accessible prompts for any choices.
- Results go to stdout; prompts and progress go to stderr.
- Every action in the full-screen UI can also be done in plain mode.

If that's too much for one release, ship accessible onboarding plus flag-driven subcommands for the main actions first. Say clearly in the docs which parts aren't covered yet.

## Testing

- **Unit test** `accessibleMode()`: flag, env and config precedence, plus `TERM=dumb`.
- **Transcript test:** run the accessible form with scripted input, including a wrong answer to check that the error text repeats correctly. Assert on the output and on the saved config.
- **Manual pass with NVDA** in Windows Terminal before release, ideally with one of the users who reported the problem. Listen for anything read twice, any symbols read aloud, and whether the user can tell setup finished.

The full-screen path stays as it is for sighted users. The one structural change is that the accessible path no longer goes through Bubble Tea at all.
