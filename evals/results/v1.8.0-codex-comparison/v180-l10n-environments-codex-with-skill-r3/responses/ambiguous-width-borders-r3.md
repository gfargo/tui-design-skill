This strongly suggests an **East Asian ambiguous-width mismatch** between your Go app and users’ terminals.

Rounded corners `╭╮╰╯`, most box-drawing characters, and bullets such as `•` and `●` belong to Unicode’s *East Asian Ambiguous* class. They commonly occupy **one terminal cell**, but some terminals can treat them as **two**. If your layout measures one cell while the terminal advances two—or vice versa—borders drift and bullet indentation breaks.

Go adds a likely trigger: **`go-runewidth` can default to wide ambiguous characters under `ja`, `ko`, or `zh` locales**, while other width libraries commonly default to narrow. The terminal’s setting is independent of the process locale, so even a Unicode-aware width function can disagree with it.

To confirm and fix it:

- Reproduce with English and Japanese locales, independently toggling the terminal’s “ambiguous characters are double-width” setting. Restart between locale changes because libraries may initialize width policy at startup.
- Check that rendering, padding, truncation, and cursor positioning all use the same terminal-cell width policy. Avoid `len()` and rune counts; in Lipgloss use `lipgloss.Width()`, while still checking its policy against the terminal.
- Provide an explicit width-policy override where your stack supports it, plus an **ASCII fallback**: `+`, `-`, `|` for borders and `*` for bullets. Switching from rounded to square Unicode borders won’t reliably solve this.
- Prefer non-ambiguous markers such as `▸` when appropriate, and test actual terminal rendering at 80×24 and in a 60-column split. String snapshots alone won’t reveal the terminal’s width disagreement.

Also remove bullets repeated on every row if they convey no useful distinction; that eliminates one fragile glyph and reduces clutter.

UTF-8 support alone doesn’t guarantee matching cell widths, and a Japanese locale doesn’t guarantee the terminal uses double-width symbols. The key is agreement between the app’s measurements and the terminal’s cursor advance.