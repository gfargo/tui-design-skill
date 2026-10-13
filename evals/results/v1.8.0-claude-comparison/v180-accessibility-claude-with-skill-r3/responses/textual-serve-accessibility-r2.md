**No. `textual serve` doesn't make the app any more accessible to screen-reader users.** Browsers are good for screen readers because web pages expose semantic HTML and ARIA through the accessibility tree. `textual serve` doesn't send that. Its browser client draws the terminal grid with xterm.js on a canvas, and xterm's screen-reader mode is turned off. The screen reader gets a grid of character cells with no headings, buttons, list items or focus semantics. That's no better than running the app in a terminal, and often worse, because a native terminal at least reports text as it's written.

The deeper problem is that this applies to any full-screen TUI, in a browser or a terminal:

- **Every redraw is read as new text.** Screen readers announce what changed. When a highlight moves, a spinner ticks or a panel repaints, the user hears it.
- **The layout carries no structure.** Panels, columns and borders are only positions on a grid, so there's nothing for a listener to navigate. Box-drawing characters are read out as symbol noise.
- **Textual itself has no screen-reader support.** The roadmap item is still open, and `textual serve` doesn't add any.

## What to do instead

Ship a **linear plain mode** next to the TUI, for example `--no-tui` or an environment variable such as `YOURAPP_ACCESSIBLE=1`. Treat it as part of the product, not a degraded fallback:

1. **Make every action reachable.** Nothing should exist only in the TUI.
2. **Add lines instead of redrawing.** Report changes as new lines, like `Saved notes.txt`, keep output in normal scrollback rather than the alternate screen, and end each command with a status line.
3. **Flatten tables and remove decoration.** Print table rows as `Header: value` lines or offer `--format csv|json`. Drop borders and ASCII art.
4. **Number the choices.** Print a numbered list and read a typed answer, rather than using arrow-key menus that get re-read whenever the highlight moves.
5. **Label lines and describe progress in words.** Use prefixes like `error:` and `warning:`, and occasional progress lines like `Uploaded 3 of 10` instead of spinners or progress bars.
6. **Let users turn it on once.** Use a flag, environment variable or saved setting, and switch it on automatically when stdout isn't a terminal. Don't rely on detecting a screen reader.
7. **Keep the streams separate.** Results go to stdout; prompts and progress go to stderr.

In the Textual app itself, set `TEXTUAL_ANIMATIONS=none` (or `App.animation_level = "none"`) for reduced motion. Custom timers and spinners need to check `app.animation_level` themselves.

Claude Code's screen-reader mode is a good published example to model on: flat text, `Header: value` tables, numbered menus, labelled lines, no full-screen mode, and the terminal bell when it needs input.

`textual serve` is still useful for putting the app in a browser tab without code changes. Just don't count it as accessibility work.
