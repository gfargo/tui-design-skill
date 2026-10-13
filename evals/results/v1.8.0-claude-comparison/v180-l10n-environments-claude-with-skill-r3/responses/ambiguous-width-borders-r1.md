Most likely this is **East Asian Ambiguous width**. Your app and your Japanese users' terminals disagree about how many columns some characters take up.

## The cause

Unicode has a class of characters whose width depends on context ([UAX #11](https://www.unicode.org/reports/tr11/tr11-46.html)). They take one cell by default but two in East Asian contexts. That class includes:

- **Nearly all box-drawing characters**, including the rounded corners `╭╮╰╯` and the lines `─│`.
- **Common bullets and markers**: `•`, `·`, `●`, `★`, `…`, and the arrows `←↑→↓`.

Those are the two things your users are reporting, which points strongly to this cause. Kanji and kana are always two cells wide, so the Japanese text itself is probably measured correctly. The problem is only these in-between characters.

The width gets decided in two places, and they can disagree:

1. **The terminal.** iTerm2, VTE-based terminals like GNOME Terminal, and Windows Terminal 1.25+ have an "ambiguous characters are double-width" setting. Japanese users often turn it on, because their CJK fonts draw these characters at two cells.
2. **Your Go width library.** `go-runewidth` (used directly or underneath older Lipgloss/Bubbles versions) automatically switches to "ambiguous = wide" when the locale (`LC_ALL`, `LC_CTYPE` or `LANG`) is `ja`, `ko` or `zh`. Most other width libraries, including the `charmbracelet/x/ansi` path in the newer Charm stack, treat them as narrow.

When the two disagree, Lipgloss pads and joins lines using a width that doesn't match what the terminal draws. Right-hand borders end up jagged, and text after a `•` shifts by a column. It can go wrong either way: a `ja_JP.UTF-8` locale with ambiguous-narrow in the terminal, or an English locale with ambiguous-wide in the terminal. On an English locale with default terminal settings, everything agrees, which is why you can't see the problem.

## Reproduce it

Turn on the ambiguous-wide setting in iTerm2 (Profiles → Text → "Ambiguous characters are double-width") and run your app. Then try again with `LANG=ja_JP.UTF-8`. Check which width library your `go.mod` actually pulls in, and which way it decides.

## Fixes, best first

1. **Stop depending on ambiguous characters for markers.** Use characters that are narrow in every setting: `▸ ▾ ✓ ✗ ⋯` and the Braille spinner frames instead of `• ● … →`. This fixes the bullet problem outright.
2. **Keep an ASCII border set one switch away.** Map `╭╮╰╯` to `+`, `─` to `-` and `│` to `|`. Lipgloss lets you define a custom `lipgloss.Border`. Expose it as `--ascii` or `MYAPP_ASCII=1`. You can't avoid ambiguous characters in Unicode borders, so this is the reliable escape hatch.
3. **Make the app's measurement match the terminal's.** If you use `go-runewidth`, `runewidth.DefaultCondition.EastAsianWidth` lets you set the mode instead of inferring it from locale. Make it configurable, because the locale doesn't tell you what the terminal is set to. Some apps detect it directly: print one ambiguous character, then ask the terminal for the cursor position (DSR, `ESC[6n`). That's more work and only worth it if Unicode borders must look right by default.

## Prevent it coming back

Add golden tests for your views under both a Japanese and an English locale, and pin the locale explicitly in tests because CI machines vary. Also do a manual pass with the terminal's ambiguous-wide setting on. That catches this whole class of bug, not just the two symptoms reported so far.
