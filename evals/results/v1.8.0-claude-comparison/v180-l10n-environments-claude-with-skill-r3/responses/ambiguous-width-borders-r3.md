You can't reproduce it because the bug only shows up when two settings disagree, and your machine never sets either one.

## What's going on

Unicode has a category called **East Asian Ambiguous** width (UAX #11). Characters in it take one cell in Western terminals and two cells in East Asian setups. Nearly all box-drawing characters are in this category, including the rounded corners `╭╮╰╯` and the lines `─│`. So are the usual bullet and marker characters: `•`, `●`, `·`, `…`, `★`, `←↑→↓`.

Two separate things decide how wide these characters are:

1. **The terminal.** iTerm2, VTE-based terminals like GNOME Terminal, and Windows Terminal 1.25+ have a setting that draws ambiguous characters two cells wide. Many Japanese users turn it on.
2. **Your Go code's width library.** This decides how many cells Lipgloss thinks each character uses when it pads text and lays out borders.
   - `go-runewidth` treats ambiguous characters as **wide** when the locale (`LC_ALL` / `LC_CTYPE` / `LANG`) is `ja`, `ko`, or `zh`.
   - Most other width libraries, including the `charmbracelet/x/ansi` measurement used by the Lipgloss v2 stack, treat them as **narrow** regardless of locale.

If the app and the terminal disagree, every border segment and bullet is off by one cell per character. Right edges become jagged, corners don't meet, and text after a bullet shifts. For you, everything is narrow on both sides, so it all lines up.

The disagreement can go either way, depending on your dependencies and the user's setup:

- **Terminal draws wide, app measures narrow.** For example, Lipgloss v2 running in iTerm2 with "ambiguous characters are double-width" turned on. Borders overflow and wrap.
- **App measures wide, terminal draws narrow.** For example, a `go-runewidth`-based stack under `LANG=ja_JP.UTF-8` in a terminal with the default narrow setting. Padding comes out short and right borders sit too far left.

## How to confirm it

Ask an affected user for:
- their terminal and whether its ambiguous-width setting is on
- `echo $LC_ALL $LC_CTYPE $LANG`
- a screenshot

Check which width library your `go.mod` actually pulls in (`go-runewidth` or `x/ansi`). Then reproduce it yourself: turn on iTerm2's ambiguous-wide option, and separately run with `LANG=ja_JP.UTF-8`.

## Fixes, in order of value

1. **Use bullets and markers from the narrow class.** Swap `•` and `●` for something like `▸`, `▾`, `✓`, `✗`, or `⋯`. Use Braille spinner frames instead of dot or star glyphs. Markers then look the same everywhere, whatever the settings.
2. **Make the ASCII border set easy to switch to.** Add `--ascii` or `MYAPP_ASCII=1` to switch to `+-|` borders (with Lipgloss, `lipgloss.Border{...}` with ASCII runes, or `NormalBorder` replaced by a custom ASCII set). Rounded corners can't be made safe, because no rounded-corner character is narrow-class. Mention the switch in help or troubleshooting docs for CJK users.
3. **Make app and terminal agree, if you want to keep the box characters.** Let users say which mode their terminal is in, for example a config option `ambiguous_width = wide|narrow`. Use that value consistently for every width calculation instead of guessing from the locale. The terminal setting can't be detected reliably from the locale, so an explicit option beats inference. If you're on `go-runewidth`, it reportedly accepts a `RUNEWIDTH_EASTASIAN=0/1` environment override. I haven't checked that here, so look at the version you use before relying on it.
4. **Never measure with `len()`.** Use `lipgloss.Width()` everywhere you pad or truncate. A single byte- or rune-based calculation will still break CJK text even after the ambiguous-width issue is fixed.

## Prevent it coming back

Add golden tests for the bordered views at 80×24 under a pinned `LANG=ja_JP.UTF-8` and under `C.UTF-8`. Include strings with CJK characters, combining marks, and emoji. Also do one manual check per release with a terminal's ambiguous-wide setting on. These cases need tests because the people who report them are the ones who notice; nobody on an English setup ever will.

If you share the border and bullet rendering code plus your `go.mod`, I can tell you which side of the mismatch you're on and make the specific change.
