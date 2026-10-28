You can't make Shift+Enter work everywhere, so don't rely on it. Treat it as a shortcut that works in some terminals, and give every user a newline key that works in all of them.

## Why Shift+Enter goes missing

Under the legacy key encoding that most terminals send by default, Shift+Enter produces the same byte as plain Enter (`\r`). Your app can't tell them apart because the difference never reaches it. They become different keys only when the terminal speaks the **kitty keyboard protocol** and your app turns it on. Kitty, foot, Ghostty, iTerm2, Alacritty 0.13+, WezTerm (with `enable_kitty_keyboard`), and Windows Terminal 1.25+ support it. Inside tmux it usually still won't arrive, because tmux's `extended-keys` option is off by default.

## What to do

**1. Bind several newline routes and accept all of them all the time:**

| Key | Why |
|---|---|
| `Shift+Enter` | The key users try first. It arrives only when the keyboard protocol is active. |
| `Ctrl+J` | Works in every terminal. It sends a line feed (`\n`), while Enter sends a carriage return (`\r`), and raw mode keeps the two separate. |
| `Alt+Enter` | Common and easy to remember. On macOS, Terminal.app and iTerm2 only send it when Option is set to act as Meta. |
| `\` then `Enter` | A shell-style fallback for anyone who never reads the hints. If the text ends in a backslash, replace the backslash with a newline instead of sending. |

**2. Turn on the keyboard protocol where it's supported.** Frameworks differ:

- **Bubble Tea v2:** on by default. Listen for `tea.KeyboardEnhancementsMsg`. It arrives only if the terminal answers, and possibly after the first frame.
- **Textual:** on by default.
- **crossterm / Ratatui:** off by default. Check `supports_keyboard_enhancement()`, then push `KeyboardEnhancementFlags::DISAMBIGUATE_ESCAPE_CODES`. You must pop the flags on every exit path, including panics, because Ratatui's `restore()` won't do it for you.
- **Ink:** opt-in through the `kittyKeyboard` render option. If you use Pastel, it calls `render()` without options, so call `render()` directly.

**3. Only advertise keys that actually work.** By default the footer or placeholder should say `Enter send · Ctrl+J newline`. Change it to `Shift+Enter newline` only after the terminal confirms the protocol (in Bubble Tea, when `msg.SupportsKeyDisambiguation()` is true). Users then never see a hint that does nothing in their terminal.

**4. Enable bracketed paste.** Pasting multi-line text must insert the newlines and never send the message. Without bracketed paste, kitty and Ghostty deliver each pasted newline as Enter, and a three-line paste becomes a sent half-message. Bubble Tea and Textual turn it on by default. With crossterm you enable it yourself, and Ink enables it only while a paste hook is mounted.

## Optional: a mode switch for long prompts

If users often write long prompts, you can flip the rule while the input holds more than one line: Enter inserts a newline and `Ctrl+Enter` or `Ctrl+S` sends. Show which mode is active in the footer. For a chat app, Enter-to-send with the fallbacks above is the better default.

## Testing it

Make your key handler return a result (send, newline, or ignore) for synthetic events: `Enter`, `Shift+Enter`, `Ctrl+J`, `Alt+Enter`, a trailing `\` followed by `Enter`, and a bracketed paste containing `\n`. Then check by hand in three places: a terminal with the protocol (Ghostty or kitty), Terminal.app, and tmux with default settings.

If you tell me which framework you're using, I can write the actual key handling code.
