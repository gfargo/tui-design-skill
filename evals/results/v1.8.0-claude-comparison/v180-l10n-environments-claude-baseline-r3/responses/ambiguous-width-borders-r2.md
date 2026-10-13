I couldn't check this against your code because the working directory is empty. But the symptom (fine for you, broken only for Japanese users, and only on box borders and bullets) almost always has one cause: **East Asian Ambiguous-width characters.**

## What's going on

Unicode (UAX #11) gives each character an East Asian Width property. Most characters are clearly narrow or wide, but some are **Ambiguous (A)**. Their display width depends on the locale and terminal:

- In Western locales they take **1 column**.
- In CJK locales, and in terminals set to "ambiguous width = double", they take **2 columns**.

Many common TUI characters are Ambiguous:

| Characters | Use |
|---|---|
| `─ │ ┌ ┐ └ ┘ ├ ┤ ┼` | box drawing (most of U+2500–257F) |
| `•` `●` `○` `◆` `■` `□` `▶` `★` `※` | bullets and markers |
| `…` `→` `←` `°` `×` `§` | misc |

(The rounded corners `╭╮╰╯` are Neutral, not Ambiguous. That mismatch is part of why rounded boxes break so visibly: corners take 1 column and edges take 2.)

So two different width calculations end up disagreeing:

1. **Your Go code** measures strings with `go-runewidth` (which lipgloss and bubbletea use) or with `uniseg`. `go-runewidth` checks `LANG`/`LC_ALL`/`LC_CTYPE` at startup. With a `ja_JP.UTF-8` locale it sets `EastAsianWidth = true` and counts Ambiguous characters as 2. Some code paths, `uniseg` among them, always count them as 1.
2. **The terminal** draws them as 1 or 2 based on its own setting: iTerm2's "Ambiguous characters are double-width", Windows Terminal, the fonts in a Japanese setup, and so on.

When those two numbers differ, padding and border lengths are calculated for one width and drawn at another. The right border drifts, bullet text shifts by a column, and lines wrap early. Your team uses an `en_US` locale with default terminal settings, so both sides say 1 and everything lines up.

## How to confirm

Ask an affected user for `echo $LANG $LC_ALL $LC_CTYPE`, their terminal, and whether its ambiguous-width setting is on. You can usually reproduce it yourself:

```sh
LANG=ja_JP.UTF-8 ./yourapp            # Go side switches to width 2
RUNEWIDTH_EASTASIAN=1 ./yourapp       # force it explicitly
RUNEWIDTH_EASTASIAN=0 ./yourapp       # force narrow
```

Combine these with toggling the iTerm2 setting and you'll see each kind of mismatch.

## Fixes, from most to least robust

1. **Avoid Ambiguous characters for structure.** Use ASCII borders/bullets (`+ - |`, `*`, `-`, `>`), or pick characters that are Neutral rather than Ambiguous. Check each one with `runewidth.IsAmbiguousWidth(r)`. This is the only option that works whatever the terminal setting is.
2. **Use one width model and let users override it.** Make sure every width calculation goes through the same library. Mixing `uniseg.StringWidth`, `runewidth.StringWidth` and `len()` makes this much worse. Then honor `RUNEWIDTH_EASTASIAN`, or add a flag or config option, so a user can match it to their terminal:
   ```go
   runewidth.DefaultCondition.EastAsianWidth = cfg.AmbiguousWide
   ```
3. **Offer an ASCII border/bullet theme** (lipgloss has `NormalBorder`, `ASCIIBorder`, and so on). Select it automatically when the locale is CJK, or let users switch to it.
4. **Detect at runtime** (advanced): print an Ambiguous character, query the cursor position with `ESC[6n`, and see whether it moved 1 or 2 columns. Then set `EastAsianWidth` to match. This is accurate but adds startup complexity.

If you point me at the repo, I can find the exact characters and width calls involved and suggest a specific change.
