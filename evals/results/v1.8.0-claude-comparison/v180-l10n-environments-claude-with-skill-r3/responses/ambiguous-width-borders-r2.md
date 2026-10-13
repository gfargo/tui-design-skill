Almost certainly this is **East Asian Ambiguous width**. Your program and your Japanese users' terminals disagree about how many cells certain characters take. You don't see it because in your setup both sides count them as one cell. I can't see your code (there are no `.go` files in this workspace), so I've written this from the symptom.

## What's going on

Unicode has a class of characters called "Ambiguous" (UAX #11). They're one cell wide by default, but two cells wide in East Asian contexts. Nearly all box-drawing characters are in it, including the rounded corners `╭╮╰╯` and the lines `─│`. So are common markers like `•`, `●`, `·`, `…`, `★` and the arrows `←↑→↓`. That matches your two symptoms exactly.

Two separate settings decide the width, and they can disagree in either direction:

1. **The terminal:** Many Japanese users enable "ambiguous characters are double-width" because CJK fonts expect it. iTerm2, VTE-based terminals like GNOME Terminal, and Windows Terminal 1.25+ all have this option. Your program still thinks `╭` is one cell, but the terminal draws it as two. Each border row pushes the right edge out, and every `•` shifts the text after it.
2. **Your width library:** `go-runewidth` treats ambiguous characters as wide whenever the locale is `ja`, `ko` or `zh` (for example `LANG=ja_JP.UTF-8`). It's used by lipgloss v1, tcell/tview, and many Bubbles versions. If the user's terminal still draws them narrow, the program pads too little and the borders come up short. Lipgloss v2 measures through `charmbracelet/x/ansi`, which treats them as narrow regardless of locale. That gives you the first failure mode instead.

On a typical English-locale machine with the terminal on its default setting, both sides say "narrow", so everything lines up.

## How to confirm

Ask an affected user for:
- `echo $LC_ALL $LC_CTYPE $LANG`
- their terminal app and whether its ambiguous-width or double-width setting is on
- a screenshot: if the right border sits **too far right**, the terminal is drawing wide and the app measured narrow. If it falls **short**, it's the reverse.

To reproduce it yourself, turn on "Ambiguous characters are double-width" in iTerm2 (Profiles → Text). Separately, run with `LANG=ja_JP.UTF-8` and the setting off.

## Fixes, in order of value

1. **Use bullet markers that are always one cell.** Replace `•`/`●`/`…`/arrows with `▸ ▾ ✓ ✗ ⋯`, which aren't in the ambiguous class. Braille spinner frames are safe too. This removes the marker misalignment no matter how the terminal is set.
2. **Make an ASCII border set easy to switch on.** Provide a `--ascii` flag or `MYAPP_ASCII=1` and map borders to `+-|`. In lipgloss, that's a custom `lipgloss.Border{...}` instead of `lipgloss.RoundedBorder()`. Box-drawing characters have no narrow-only equivalent, so ASCII is the only border that stays aligned for everyone.
3. **Make your width calculation match the terminal.** Your Go code can't ask the terminal which setting is on, so let the user tell you:
   - If you're on `go-runewidth`, set `runewidth.DefaultCondition.EastAsianWidth` explicitly from your config instead of relying on the locale guess. It also reads a `RUNEWIDTH_EASTASIAN=0/1` environment variable, which works as a quick workaround for users.
   - On lipgloss v2 / `x/ansi`, ambiguous characters are always counted as one cell. Users with double-width turned on will need the ASCII borders from step 2, or need to turn that setting off.
4. **Keep it from coming back.** Add golden tests that render the view with CJK content under both `LANG=C.UTF-8` and `LANG=ja_JP.UTF-8`, and pin the locale in CI. Do one manual check with the terminal's double-width setting on. Measure everything with `lipgloss.Width()`, never `len()`.

Steps 1 and 2 are the main fix. Step 3 is for users who want the rounded borders and are willing to set one option.
