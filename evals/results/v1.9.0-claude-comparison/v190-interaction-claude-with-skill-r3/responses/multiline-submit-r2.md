**Short answer:** Shift+Enter is not a reliable newline key. Keep it as a bonus where the terminal supports it, but always accept a fallback that works everywhere, and show users which key that is.

## Why Shift+Enter fails

Most terminals still use the old key encoding by default. In that encoding, Enter sends a carriage return (`\r`), and **Shift+Enter sends the same `\r`**. Your app gets identical bytes for both keys, so it cannot tell them apart. That is a limit of the encoding, not a bug in your code.

The kitty keyboard protocol fixes this. Push flag 1 (`CSI > 1 u`) on startup and pop it (`CSI < u`) on exit, and Shift+Enter arrives as its own key. Terminals that support it include kitty, foot, Alacritty 0.13+, Ghostty, iTerm2, WezTerm (with `enable_kitty_keyboard`), Warp, Rio, and Windows Terminal 1.25+. It is **off inside tmux** unless the user sets `extended-keys`, and older terminals, the Linux console, and many SSH setups don't have it at all.

## What to bind

| Action | Binding | Works where |
|---|---|---|
| Send | `Enter` | Everywhere |
| Newline (bonus) | `Shift+Enter` | Only when the kitty protocol is active |
| Newline (main fallback) | `Ctrl+J` | Everywhere: it sends a line feed (`\n`), which differs from Enter's `\r` even in the old encoding |
| Newline (second fallback) | `Alt+Enter` | Almost everywhere (it arrives as Esc followed by `\r`) |
| Newline (third route) | Type `\` at the end of the line, then `Enter` | Everywhere, and easy to guess |

Accept all of these at the same time. Don't make one depend on detecting the terminal. The terminal's answer to the capability query can arrive after your first frame, or never.

## Make the newline key visible

Show it in the placeholder or footer. Base the hint on what the terminal actually reported:

```
 > Type a message…                    Enter send · Ctrl+J newline
```

Only change the hint to `Shift+Enter newline` after the terminal confirms the kitty protocol.

## Two related fixes

- **Turn on bracketed paste (`CSI ? 2004 h`).** Without it, a pasted multi-line block arrives as typed text, so each newline acts like Enter and sends partial messages. That is often the real bug behind "it sent my message halfway through." With it on, pasted newlines are inserted into the field and never trigger a send.
- **Clean up on every exit path.** That means popping the keyboard flags and turning bracketed paste off, including after errors and panics. Otherwise the user's shell is left in a mode it doesn't understand.

## By framework

- **Bubble Tea v2:** turns on the kitty protocol for you. Always accept both `shift+enter` and `ctrl+j`. Show the Shift+Enter hint only after `tea.KeyboardEnhancementsMsg` reports `SupportsKeyDisambiguation()`.
- **crossterm / Ratatui:** the protocol and bracketed paste are off by default. Turn them on with `PushKeyboardEnhancementFlags(DISAMBIGUATE_ESCAPE_CODES)` and `EnableBracketedPaste`, and undo both yourself on exit.
- **Textual:** turns on both by default.
- **Ink:** the kitty protocol is opt-in, and bracketed paste is only on while a paste hook is mounted.

If you tell me which framework you're using, I can write the exact key-handling code.
