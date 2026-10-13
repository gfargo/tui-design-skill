This is likely an **East Asian Ambiguous character-width mismatch**.

Rounded box corners such as `╭ ╮ ╰ ╯` and the bullet `•` have Unicode width class “Ambiguous.” Many terminals display them as **one column**, while terminals configured for Japanese text may display them as **two columns**. If your Go TUI calculates one column but the terminal draws two—or vice versa—borders and markers stop lining up.

Check both sides:

- **Go width calculation:** libraries such as `go-runewidth` can choose ambiguous widths based on locale or configuration. Look at `LANG`, `LC_CTYPE`, and any `EastAsianWidth` setting.
- **Users’ terminal settings:** look for “ambiguous characters are double-width” or a similar option. Locale and terminal behavior don’t always agree.
- **Layout code:** `len(s)` counts bytes, and counting runes still doesn’t give display columns. Use a terminal display-width library consistently.

For a broadly compatible fallback, offer ASCII borders (`+`, `-`, `|`) and markers (`*` or `-`). If you retain the Unicode styling, make ambiguous-width handling configurable and ensure it matches the terminal.

A Japanese locale alone doesn’t prove the cause, but these particular characters are a strong clue.