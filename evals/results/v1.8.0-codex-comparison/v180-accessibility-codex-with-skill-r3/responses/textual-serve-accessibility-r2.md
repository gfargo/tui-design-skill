**No—`textual serve` doesn’t make a Textual app accessible to screen-reader users.** It provides browser access, but it doesn’t turn Textual widgets into semantic HTML controls.

As the tui-design skill explains, the browser client renders a terminal grid using xterm.js on a canvas, with its screen-reader mode off. Screen readers therefore don’t get labelled buttons, form fields, table structure, or meaningful focus announcements. Browsers’ accessibility support depends on the page exposing that information.

For your app, I recommend:

- **A `--no-tui` mode** covering every workflow: append-only text, labelled values, numbered choices, ordinary line-input prompts, and explicit success/error messages.
- **A semantic HTML interface** if browser access is the goal, sharing the same business logic with your Textual app.

Keyboard support, reduced motion (`TEXTUAL_ANIMATIONS=none`), and color-independent cues help, but they don’t replace screen-reader support. Validate the chosen interface with actual screen readers and screen-reader users.