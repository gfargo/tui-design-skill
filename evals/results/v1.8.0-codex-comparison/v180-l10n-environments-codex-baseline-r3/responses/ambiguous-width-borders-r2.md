This is probably a **Unicode East Asian Ambiguous width mismatch**.

Rounded border characters such as `╭ ╮ ╰ ╯` and the bullet `•` have ambiguous width: some terminals render them as **one column**, while terminals configured for East Asian text may render them as **two columns**. If your Go TUI counts each as one column, its padding and cursor positions no longer match what the terminal draws.

That explains why it works for you but breaks for some Japanese users. The deciding factor is the terminal’s width configuration, sometimes influenced by locale—not the user’s language alone.

To address it:

- Check your width library, often `go-runewidth` or a dependency used by your TUI framework. Its ambiguous-width setting must match the terminal.
- Offer a width setting users can override; locale detection isn’t always reliable.
- Provide an ASCII fallback for borders and bullets (`+`, `-`, `|`, `*`) for predictable alignment.

Also ensure layout uses **terminal display width**, not `len(s)` or rune count. Neither correctly measures how many screen columns Unicode text occupies.