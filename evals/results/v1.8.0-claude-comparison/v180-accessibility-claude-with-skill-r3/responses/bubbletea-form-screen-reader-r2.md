Huh's accessible mode is the fix. The catch is that it only works when Huh runs the form itself. My guess at why it isn't working today: while Bubble Tea is driving the form, NVDA can't follow it.

## Why NVDA fails today

- **Every keypress redraws the screen.** NVDA spots new text in a terminal by comparing the screen before and after. In a full-screen form, moving the highlight in a Select or redrawing a field counts as new text, so it gets read out again. Box-drawing and other styling are read as symbol noise.
- **The alternate screen has no scrollback.** Users can't review earlier questions and answers.
- **The cursor isn't on the focused field.** Screen readers follow the terminal cursor, and full-screen apps usually hide it or park it somewhere else.
- **`WithAccessible(true)` can't help an embedded form.** Accessible mode skips Bubble Tea and asks one plain question per line. If your parent model passes messages to `form.Update` and draws `form.View()` inside its own view, there's no Bubble Tea loop for Huh to skip. Setting the flag on an embedded form won't give you the linear prompts. Huh also only switches it on by itself when `TERM=dumb`, which an NVDA user won't have set.

## The fix

**1. In accessible mode, run onboarding with `form.Run()` outside your Bubble Tea program.** Onboarding usually happens first, so do it before you start `tea.NewProgram`:

```go
form := buildOnboardingForm(&cfg) // the same form you embed today

if cfg.Accessible {
    if err := form.WithAccessible(true).Run(); err != nil {
        return err
    }
    // continue in linear mode (see step 4)
} else {
    // existing path: embed the form in the full-screen Bubble Tea app
}
```

Build the form once and pick how to run it, so the two paths can't drift apart. In accessible mode the user gets:
- a numbered list for each `Select`, answered by typing a number;
- for `MultiSelect`, numbers typed one at a time to toggle choices, then `0` to finish;
- `y`/`n` for `Confirm`;
- validation errors printed as text, then the question again.

Nothing gets redrawn, and everything stays in scrollback.

If onboarding can also start partway through a session, the program has to give up the terminal first. `tea.ExecProcess` does that for child processes. For an in-process form, the low-level `p.ReleaseTerminal()` / `p.RestoreTerminal()` pair is the escape hatch. Running onboarding before the program starts is much simpler, so prefer that.

**2. Let users turn it on explicitly. Don't try to detect a screen reader.** You can't reliably detect one, and gh, Claude Code, and Ink all require an opt-in. Offer:
- a `--accessible` flag;
- an environment variable, e.g. `YOURAPP_ACCESSIBLE=1` (gh uses `GH_ACCESSIBLE_PROMPTER`);
- a saved config key, so it's set once and not on every run;
- automatic linear mode when stdin or stdout isn't a terminal.

Mention the flag in `--help` and on the first screen of the TUI, because blind users can't find it by exploring the full-screen UI.

**3. Give every onboarding answer a flag or config equivalent.** For example: `yourapp init --name … --region … --yes`. That lets users skip the prompts entirely and lets scripts run onboarding unattended.

**4. Don't stop at onboarding.** Bubble Tea and Bubbles have no screen-reader support, so once onboarding works, users will hit the same wall in the main app. In linear mode, follow these rules everywhere:
- **Append instead of redrawing.** Report changes as new lines (`Saved config to ~/.config/yourapp.toml`) rather than updating a status bar.
- **Replace spinners.** Print `Working…` once, then a final status line, and use occasional progress lines (`Synced 3 of 10`) instead of spinner frames. Add a `YOURAPP_SPINNER_DISABLED`-style switch like gh's.
- **Flatten tables.** Use `Header: value` lines or `--format json|csv`, with no borders.
- **Label lines.** Prefix with `error:` / `warning:`, and phrase errors so they make sense read aloud: what failed and what to do next.
- **End every command with a status line,** so success is never silent.
- **Keep the streams separate.** Results go to stdout; prompts and progress go to stderr.

## Checking it

- **Automated:** test the accessible path by feeding scripted answers to the form and checking the resulting config. Cover a wrong answer (out-of-range number, empty required field) and confirm the error is printed as text and the question repeats.
- **Golden test:** snapshot the plain-mode transcript and assert it has no ANSI escape codes or box-drawing characters.
- **Manual (can't be skipped):** run it with NVDA in Windows Terminal, and ideally have one of the users who reported the problem try it. Things to check:
  - each question is read once;
  - choices are read as a numbered list;
  - errors are announced;
  - answers can be reviewed in scrollback afterwards.

I don't have your code, so this is based on the usual way Huh forms get embedded. Before changing anything, check that the onboarding form is driven through `form.Update` inside your model and not through `form.Run()`. If it already uses `form.Run()`, the problem is probably narrower, e.g. accessible mode is never actually switched on. Either way, the changes are the same: an explicit opt-in, linear prompts, flags for every answer, and a plain mode for the rest of the app.
