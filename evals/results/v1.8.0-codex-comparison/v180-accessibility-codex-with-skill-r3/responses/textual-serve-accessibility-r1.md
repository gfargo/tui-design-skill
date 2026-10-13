**No—`textual serve` is a deployment option, not a screen-reader accessibility solution.**

As the tui-design skill explains, its browser client renders a terminal grid using xterm.js on a canvas, with xterm’s screen-reader mode disabled. It doesn’t turn Textual widgets into semantic HTML buttons, headings, or form fields. Browsers’ screen-reader support depends on that accessible structure; merely running inside a browser doesn’t provide it.

For your app, prioritize:

- **A complete `--no-tui` mode:** append-only text, labelled values, numbered choices, explicit success/error messages, and no borders, spinners, or screen repainting. Make every TUI action available there.
- **A semantic HTML interface** if browser accessibility is the goal, sharing the same application logic.
- **Testing real workflows with screen-reader users**, including navigation, input, errors, and completion.

Keyboard navigation and reduced motion help, but they don’t supply the missing screen-reader semantics.