This is likely an **East Asian ambiguous-width mismatch** between your Go app and users’ terminals.

Rounded corners `╭╮╰╯`, most box-drawing characters, and bullets such as `•` and `●` belong to Unicode’s *East Asian Ambiguous* class. They can occupy **one or two terminal cells**. If your app measures one cell while the terminal renders two—or vice versa—padding, borders, and marker alignment break.

The Go-specific trap: **`go-runewidth` defaults to wide ambiguous characters under Japanese, Korean, and Chinese locales**, while many other width libraries default to narrow. A Japanese locale and the terminal’s “ambiguous characters are double-width” setting can therefore produce different assumptions. UTF-8 support alone doesn’t resolve this.

To confirm and fix it:

- Reproduce with `ja_JP.UTF-8`, toggling the terminal’s ambiguous-width setting. Check the app’s width library and effective locale (`LC_ALL`, then `LC_CTYPE`, then `LANG`).
- Use one consistent terminal-cell measurement policy for layout, padding, truncation, and rendering. In Lipgloss, use `lipgloss.Width()`, never `len()`; ensure its policy agrees with the terminal.
- Offer an explicit width-policy override where supported, plus `--ascii`: borders `+|-`, bullets `*` or `-`. Switching rounded borders to square Unicode borders won’t solve this.
- Consider narrow-class markers such as `▸` where appropriate. Remove decorative bullets repeated on every row if they convey no useful distinction.
- Test both width modes at **80×24 and 60 columns**, including Japanese text, combining marks, and emoji.

The key is to match the terminal’s cell-width behavior; the user’s language alone cannot reliably tell you that behavior.