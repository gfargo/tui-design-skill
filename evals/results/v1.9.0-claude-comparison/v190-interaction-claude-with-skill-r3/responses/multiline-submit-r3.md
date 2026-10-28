**Keep Shift+Enter, but don't make it the only newline key.** Bind three ways to insert a newline: Shift+Enter, Alt+Enter, and Ctrl+J. Also accept a trailing `\` followed by Enter. Then show in the UI which newline key works in the user's terminal.

## Why Shift+Enter goes missing

The legacy terminal key encoding has no way to send Shift+Enter. It arrives as the same byte as plain Enter (`\r`), so your app can't tell them apart. It only becomes a separate key when the terminal supports the **kitty keyboard protocol** and your app turns it on. Terminals that support it include kitty, foot, Alacritty 0.13+, Ghostty, iTerm2, WezTerm (needs `enable_kitty_keyboard`) and Windows Terminal 1.25+.

Even in those terminals it can fail when:
- **tmux** is in the way. Its `extended-keys` option is off by default, so your app gets the legacy encoding.
- **Your framework doesn't turn the protocol on.** Bubble Tea v2 and Textual turn it on. Ink needs the `kittyKeyboard` render option. crossterm/Ratatui needs you to push `KeyboardEnhancementFlags` yourself, and pop them on every exit path.

So treat Shift+Enter as a shortcut for terminals that support it, not as the main route.

## Key bindings

| Key | Action | Works where |
|---|---|---|
| `Enter` | Send | Everywhere |
| `Shift+Enter` | Newline | Kitty-protocol terminals only |
| `Alt+Enter` | Newline | Nearly everywhere (sent as Esc + `\r`) |
| `Ctrl+J` | Newline | Everywhere: it's a line feed (`\n`), which is a different byte from Enter's `\r` |
| `\` then `Enter` | Delete the `\` and insert a newline | Everywhere, and easy to guess |

Handle all of these at all times, not only after you detect protocol support:

```text
on key:
  shift+enter | alt+enter | ctrl+j  → insert "\n"
  enter:
    if text before cursor ends with "\" → delete it, insert "\n"
    else if not composing (IME)       → send
on paste (bracketed):                 → insert text as-is, never send
```

## Also fix pasting

Turn on **bracketed paste**. Without it, kitty and Ghostty deliver each pasted newline as an Enter, so pasting a multi-line snippet sends the first line on its own. Bubble Tea and Textual turn it on by default. In Ink, use `usePaste`. In crossterm, use `EnableBracketedPaste` and turn it off again on exit.

## Show the newline key that works

Users can't guess which newline key works in their terminal, so put it in the placeholder or footer:

```
╭──────────────────────────────────────────────────────────╮
│ Message…                                                 │
╰──────────────────────────────────────────────────────────╯
 Enter send · Alt+Enter newline                    ? help
```

Start with the hint for the fallback key, which works everywhere. Switch it to `Shift+Enter newline` only after the terminal confirms protocol support. In Bubble Tea v2 that's when `tea.KeyboardEnhancementsMsg` arrives with `SupportsKeyDisambiguation()` true; that message may come after the first frame or never. In other frameworks, query with `CSI ? u` and use a timeout. At 60 columns, shorten the hint to `⏎ send · ⌥⏎ newline`; never drop the newline key from it.

## Check these

- **Inside tmux:** confirm that Alt+Enter and Ctrl+J insert a newline and Enter sends. If you document Shift+Enter, add the line `set -g extended-keys on` for users' `tmux.conf`.
- **Paste:** pasting three lines inserts three lines and sends nothing.
- **IME:** pressing Enter to confirm a CJK candidate must not send the message.
- **Exit:** if you pushed kitty flags yourself (crossterm), pop them on every exit path, including panics. Otherwise the user's shell keeps getting the enhanced key encoding.

Tell me your framework (Bubble Tea, Ratatui, Textual or Ink) and I can write the exact handler and setup.
