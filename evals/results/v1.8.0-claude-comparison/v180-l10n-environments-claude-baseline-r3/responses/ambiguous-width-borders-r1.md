The working directory is empty, so I can't look at your code. I'm fairly confident about the cause anyway, because this symptom (fine for you, broken for Japanese users, only borders and bullets affected) has a well-known explanation.

## Cause: East Asian "Ambiguous" width characters

Unicode marks some characters as **East Asian Width = Ambiguous (A)**. They're 1 column wide in Western terminals and **2 columns wide in CJK terminals or locales**. The list includes most of what TUIs use for decoration:

- Box drawing: `─ │ ╭ ╮ ╰ ╯ ┌ ┐ └ ┘ ├ ┤`
- Bullets and markers: `• ● ○ ◆ ◇ ■ □ ▲ ▼ ★ ※`
- Arrows and more: `→ ← ↑ ↓`, `…`, `°`, `×`, `§`, Greek and Cyrillic letters

Two things go wrong at once:

1. **The terminal draws them 2 cells wide.** iTerm2 has "Ambiguous characters are double-width", Windows Terminal and many Japanese terminal setups (mlterm, some PuTTY configs) do the same, and so do some fonts.
2. **Your Go width math counts them as 1, or counts differently from the terminal.** Lip Gloss and Bubble Tea measure strings with `github.com/mattn/go-runewidth` (or `uniseg`/`displaywidth` in newer versions). go-runewidth decides how to treat ambiguous characters from `RUNEWIDTH_EASTASIAN` and from the locale (`LANG`/`LC_ALL` = `ja_JP.UTF-8` → `EastAsianWidth = true`). If that decision doesn't match the terminal's setting, padding and border lengths are off by one column for every ambiguous character. The right border of a box then gets pushed out or pulled in, and lines with bullets drift.

You don't see it because your locale is probably `en_US` and your terminal renders these characters 1 wide. The two agree, so everything lines up.

## Confirming it

Ask an affected user for their `echo $LANG $LC_ALL $RUNEWIDTH_EASTASIAN`, their terminal and its ambiguous-width setting, and their font. You can usually reproduce it yourself:

- iTerm2: Profiles → Text → enable "Treat ambiguous-width characters as double width", and/or
- run with `LANG=ja_JP.UTF-8` or `RUNEWIDTH_EASTASIAN=1`

Try both mismatched combinations (terminal on with the env var off, and the reverse). Each one breaks alignment in a different direction.

## Fixes, most robust first

1. **Don't use ambiguous characters in layout-critical places.** This is the only fix that works in every terminal.
   - Bullets: use ASCII (`-`, `*`, `>`) or characters with Narrow width. Note that `•` (U+2022) and `●` are Ambiguous; `·` (U+00B7) is Ambiguous too, so test carefully.
   - Borders: `lipgloss.RoundedBorder()` uses `╭─╮│`, which are all Ambiguous. Offer an ASCII border (`+ - |`) as a fallback, or don't put content after a right border that has to align.
2. **Make your width calculation match the terminal.** If you use go-runewidth directly, set `runewidth.DefaultCondition.EastAsianWidth` explicitly instead of trusting locale detection, and expose it as a user setting or env var (e.g. `MYAPP_AMBIGUOUS_WIDE=1`). Your app can't detect what the terminal actually does, so the user has to be able to tell it.
   - Optional runtime probe: print an ambiguous character, query the cursor position with `ESC[6n`, and check whether the cursor moved 1 or 2 columns. This works in most terminals but adds complexity.
3. **Provide an ASCII or "compat" mode.** Many CJK-friendly TUIs (htop, tmux configs, various Go CLIs) have a flag that switches all decorative glyphs to ASCII. It's cheap to add and lets affected users fix the problem themselves.
4. **Check that every width calculation goes through the same function.** If any code uses `len(s)` or `utf8.RuneCountInString` for padding, Japanese text (full-width, 2 columns per character) will also misalign. Use `lipgloss.Width()` / `runewidth.StringWidth()` everywhere.

If you point me at the repo, I can find the specific glyphs and width calls involved and suggest concrete changes.
