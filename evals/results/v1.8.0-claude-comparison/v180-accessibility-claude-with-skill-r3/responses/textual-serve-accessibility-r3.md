No. `textual serve` doesn't make the app any more accessible to screen-reader users than running it in a terminal.

## Why the browser doesn't help

Browsers support screen readers well when a page has real HTML: headings, buttons, lists and ARIA roles. `textual serve` doesn't produce that. Its browser client uses xterm.js to draw the terminal's character grid onto a `<canvas>`, and xterm.js's screen-reader mode is turned off. The screen reader gets a picture of a terminal, not buttons, lists or headings. Textual has no screen-reader support of its own either; that item is still open on its roadmap.

Even if you turned on xterm.js's screen-reader mode, the main problem would remain. A full-screen TUI redraws constantly. Screen readers announce changed text, so every spinner frame, moved highlight and redrawn panel gets read out as new content. The layout also has no structure a listener can move through. No TUI framework solves this, and putting it in a browser doesn't either.

## What works instead

Add a **linear plain mode** next to the Textual UI (e.g. `--plain`, an env var, or a config setting) and treat it as part of the product, not a fallback:

- **Every action is reachable.** Nothing should be available only in the TUI.
- **Add lines instead of redrawing.** Report changes as new lines (`Saved notes.txt`) instead of updating a status bar, and stay off the alternate screen.
- **State results in words.** End each command with a status line. Show progress as an occasional line (`Uploaded 3 of 10`), not a spinner or bar.
- **Flatten tables.** Print rows as `Header: value` lines, or offer `--format csv|json`. Drop borders and box-drawing characters, which get read out as symbol noise.
- **Number the choices.** Use numbered menus with a typed answer instead of arrow-key highlights, which get re-read on every move.
- **Label lines.** Start lines with `error:`, `warning:` and so on, so a listener knows what kind of line it is before hearing it.
- **Make it opt-in and persistent.** Users switch it on once, and it also turns on automatically when stdout isn't a terminal. Don't rely on detecting a screen reader.

Claude Code's screen-reader mode is a good published example of these rules.

## Reduced motion

Textual does help here. `TEXTUAL_ANIMATIONS=none` (or `App.animation_level = "none"`) makes built-in animations skip to their end state. Your own timers and spinners need to check `app.animation_level` themselves.

If you need a browser version for other reasons, `textual serve` is fine for that. It just shouldn't be your accessibility plan.

These details come from the tui-design skill's notes on Textual and accessibility. I didn't check them against the current Textual or xterm.js source, so check that before you document anything publicly.
