No. `textual serve` won't make your app accessible to screen-reader users. It puts the same terminal UI in a browser tab, so a screen reader gets about as much as it would in a terminal.

**Why the browser doesn't help:**
- **There's no web page underneath.** Browsers read the DOM well: headings, buttons, form labels, ARIA roles. `textual serve` doesn't build that DOM. Its browser client is xterm.js, which draws the terminal's character grid onto a canvas. xterm's screen-reader mode is off, and a canvas has nothing a screen reader can navigate.
- **Textual itself has no screen-reader support.** It has no accessibility tree and no widget roles, so there's no structure for any frontend to pass along. Textual's roadmap item for screen-reader support is still open.
- **A full-screen UI is a poor fit for screen readers anyway.** Screen readers announce text that changes on screen. A full-screen app redraws all the time, so spinner frames, a highlight moving through a menu, or a redrawn panel are all read out as new text, and the layout gives the listener nothing to navigate by. No TUI framework solves this. Serving the app in a browser doesn't either.

**What works instead: a linear "plain" mode alongside the TUI.** This is what Claude Code's screen-reader mode, gh's accessible prompter, and Huh's accessible mode do:
- **Add new lines instead of redrawing.** Report a change as a line like `Saved notes.txt` rather than updating a status bar, and keep output in normal scrollback instead of a full-screen view.
- **Describe progress in words.** Print an occasional line like `Uploaded 3 of 10` instead of a spinner or bar, and end every command with a status line.
- **Flatten tables.** Print rows as `Header: value` lines or offer `--format csv|json`. Leave out borders and box-drawing characters, which are read aloud as symbol noise.
- **Number the choices.** Print a numbered list and read the typed answer, instead of an arrow-key menu that gets re-read every time the highlight moves.
- **Label lines.** Start lines with `error:` or `warning:` so a listener knows what kind of line it is before hearing it.
- **Cover every action.** Plain mode must reach everything the TUI can do, with no TUI-only actions, and every prompt needs a flag or config equivalent.
- **Make it easy to turn on.** Use a flag such as `--plain`, an environment variable, or a saved setting, and enable it automatically when stdout isn't a terminal. Don't count on detecting a screen reader.

**Things Textual does give you:**
- **Reduced motion:** `TEXTUAL_ANIMATIONS=none` (or setting `App.animation_level = "none"`) stops built-in animations. Your own timers and spinners need to check `app.animation_level` themselves.
- **Keyboard and color:** make every action reachable by keyboard, show focus with something besides color (such as reverse video, a marker, or border weight), and keep a 16-color theme so users' high-contrast terminal palettes still apply.

`textual serve` is still useful for demos or for giving people browser access to the app. Just don't count it as your accessibility support. If you share how the app is structured, I can sketch a plain mode for its main flows.
