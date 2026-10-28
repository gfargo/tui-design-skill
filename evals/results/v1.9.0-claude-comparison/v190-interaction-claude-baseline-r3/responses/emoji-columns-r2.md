## Why it happens

The two symbols look alike but they're encoded differently:

| Glyph | Codepoints | What width libraries (`wcwidth`) say | What terminals actually draw |
|---|---|---|---|
| ✅ | `U+2705` | 2 (it's an emoji by default) | 2, almost everywhere |
| ⚠️ | `U+26A0` + `U+FE0F` | usually **1** (`U+26A0` is a narrow text symbol, and the `FE0F` variation selector counts as 0) | **1 or 2**, depending on the terminal |

`U+FE0F` (variation selector 16) asks the terminal to draw the character as a color emoji. Terminals handle that request differently:

- **iTerm2, WezTerm, Kitty, and newer VS Code** honor it and draw ⚠️ two cells wide.
- **Terminal.app, older xterm/VTE, many tmux setups, and Windows conhost** ignore it for layout and give it one cell. Sometimes the glyph still spills into the next cell.
- **tmux** keeps its own width table, which can disagree with the outer terminal. Then the cursor drifts and redraws break.

Your padding code calculates one width while the terminal draws another, so every row with ⚠️ is off by one cell. The rows with ✅ come out right because everyone agrees ✅ is 2 wide.

There's also a smaller issue: some terminals have an "ambiguous-width characters are wide" setting, which shifts symbols like `⚠`, `✓`, and `●` again.

## What to do

You can't fix this by measuring more carefully, because the terminal decides the width and your program can't see that decision. Pick symbols whose width every terminal agrees on:

1. **Best option: use narrow, unambiguous symbols plus color.**
   ```
   ✓ ok      (U+2713, green)
   ! warn    (plain ASCII, yellow)
   ✗ fail    (U+2717, red)
   ```
   These are 1 cell wide everywhere that matters, and adding a text label keeps the column readable without color.

2. **If you want emoji, use only "default emoji" codepoints with no `FE0F`.** For example: ✅ `U+2705`, ❌ `U+274C`, ⛔ `U+26D4`, 🟡 `U+1F7E1`, 🔶 `U+1F536`. These are reliably 2 cells wide. Avoid anything that needs `FE0F` to look like an emoji, such as ⚠️, ✔️, ℹ️, or ❤️.

3. **Put the status column last.** If its width is off, nothing to the right of it gets pushed out of line. This is cheap insurance even after you switch symbols.

4. **Offer an ASCII fallback** (`--ascii` or `NO_EMOJI=1`) for CI logs, Windows consoles, and screen readers.

5. **If you keep emoji, measure with a library that handles them.** Use `string-width` in Node, `unicode-width` in Rust, or `wcwidth`/`rich` in Python. Don't rely on `len()` or `str.length`. Even so, only option 2's symbols will measure and render consistently.

If you share the code that renders the table, I can point out exactly where to change the symbols or the width calculation.
