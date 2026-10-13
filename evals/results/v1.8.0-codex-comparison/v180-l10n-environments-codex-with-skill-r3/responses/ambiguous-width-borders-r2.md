This is most likely an **East Asian ambiguous-width mismatch**: your app and the user’s terminal disagree about whether a character occupies one or two cells.

Rounded corners `╭╮╰╯`, most box-drawing characters, and bullets such as `•` and `●` belong to Unicode’s *East Asian Ambiguous* class. They usually occupy one cell, but terminals can treat them as two.

Go adds a particular trap: **`go-runewidth` can select wide behavior under Japanese, Korean, or Chinese locales**, while the terminal may still render those characters narrowly. The reverse mismatch is possible too. Padding, cursor positions, and borders then drift—even though everything aligns on your machine.

To diagnose and fix it:

- Check the affected user’s terminal “ambiguous characters are double-width” setting and effective locale: first nonempty `LC_ALL`, `LC_CTYPE`, then `LANG`.
- Inspect which width library your framework actually uses. Keep measurement, padding, truncation, and rendering on the same width policy, with an explicit override; locale alone cannot tell you the terminal’s setting.
- Offer `--ascii` borders using `+`, `-`, `|` and markers using `*` or `>`. Switching from rounded to square Unicode corners won’t reliably fix it.
- Test both ambiguous-width settings with Japanese and English locales, including 80×24 and a 60-column split. Plain text snapshots alone won’t reveal how a real terminal advances its cursor.

If bullets decorate every row without conveying state, remove them; that also eliminates one source of width trouble.