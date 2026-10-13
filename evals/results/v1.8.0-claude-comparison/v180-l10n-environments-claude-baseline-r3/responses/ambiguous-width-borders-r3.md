The working directory is empty, so I couldn't look at your code. This is a very well-known problem, though, and it fits your symptoms closely.

## Likely cause: "East Asian Ambiguous" width characters

The characters you use for rounded borders (`╭ ╮ ╰ ╯ ─ │`) and common bullets (`•`, `●`, `○`, `※`, `→`, `…`) are classified as **Ambiguous** width (category "A") in Unicode's East Asian Width table. That means:

- In Western locales, terminals draw them **1 cell wide**.
- In CJK setups, many terminals and fonts draw them **2 cells wide**. This includes Japanese locales, Windows Terminal or iTerm2 with the "ambiguous characters are double-width" option turned on, and fonts like MS Gothic and Osaka.

Your Go code works out widths with `go-runewidth`, which Lip Gloss and Bubble Tea use under the hood. go-runewidth also guesses from the locale. If `LANG`/`LC_ALL` is `ja_JP.UTF-8` (or `RUNEWIDTH_EASTASIAN=1` is set), it sets `EastAsianWidth = true` and counts these characters as 2. Your width maths and the terminal's drawing then disagree, either in one direction or the other:

- **Your code counts 1 but the terminal draws 2.** For example, the user's locale is `C`/`en_US`, but their terminal is set to draw ambiguous characters double-width. The right border gets pushed out and lines wrap.
- **Your code counts 2 but the terminal draws 1.** For example, the locale is `ja_JP`, but the terminal or font draws them narrow. Padding comes out short and borders land too far left.

In both cases, every line that has a border or bullet ends up shifted by one cell per ambiguous character. That's the misalignment they're seeing. You don't see it because, on an English locale, both sides agree on 1.

## How to confirm
Ask an affected user for:
- `echo $LANG $LC_ALL $LC_CTYPE $RUNEWIDTH_EASTASIAN`
- Their terminal and font, and whether a setting like "Ambiguous-width characters: double" (iTerm2, Windows Terminal, etc.) is turned on.

You can also reproduce it yourself by running with `LANG=ja_JP.UTF-8` or `RUNEWIDTH_EASTASIAN=1`, and/or turning on double-width ambiguous characters in your terminal.

## Fixes, from most to least robust
1. **Avoid ambiguous-width characters in the chrome.** Use ASCII or characters that are reliably narrow:
   - Bullets: `-`, `*`, `>`
   - Borders: `lipgloss.NormalBorder()` still uses box-drawing characters, which are also ambiguous. The only fully safe choice is an ASCII border (`+ - |`), which you can offer as a fallback style.
2. **Make your width maths match the terminal.** You can't reliably detect what the terminal will do, but you can make the choice consistent and let users change it:
   ```go
   import "github.com/mattn/go-runewidth"
   // e.g. driven by a flag/config/env var
   runewidth.DefaultCondition.EastAsianWidth = cfg.AmbiguousWide
   ```
   Set this before any rendering. Lip Gloss measures text through go-runewidth, so its layout will follow the setting.
3. **Offer a config option, like `--ascii` or `border_style = "ascii"`**, and document it for CJK users. Many popular TUIs (htop, tmux themes, lazygit) do this for exactly this reason.

A side note: if any of your layout code uses `len(s)` or `utf8.RuneCountInString` to measure widths, that's a separate bug. It will break on actual Japanese text, which is genuinely 2 cells wide. Use `lipgloss.Width` or `runewidth.StringWidth` instead.

If you point me at the code, I can find exactly which characters and width calculations are involved.
