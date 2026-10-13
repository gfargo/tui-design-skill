This is likely **Unicode East Asian Ambiguous width** handling.

Rounded border characters such as `╭ ╮ ╰ ╯` and the bullet `•` have ambiguous display width. Your TUI’s width library may count them as **one terminal cell**, while Japanese users’ terminals may render them as **two cells**, depending on terminal settings. That disagreement shifts borders and markers even though the text is identical.

To confirm, have an affected user check their terminal’s “ambiguous characters are double-width” setting. Locale can influence the behavior, but terminal configuration is the key.

For your Go TUI:

- Check which width rules your rendering library uses and whether they match the terminal.
- Offer an ASCII fallback (`+`, `-`, `|`, `*`) for predictable alignment.
- Don’t assume switching from rounded to square Unicode borders fixes it; many box-drawing characters are also ambiguous.

I didn’t find source files in the workspace, so I couldn’t verify your particular rendering library.