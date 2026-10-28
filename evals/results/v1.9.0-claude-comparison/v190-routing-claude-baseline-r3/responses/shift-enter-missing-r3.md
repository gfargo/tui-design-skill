There's no code in this directory, so this answer covers how terminals handle the key in general, not your specific framework.

## Why it happens

In a traditional terminal, Enter and Shift+Enter both send the same byte, `\r` (0x0D). The Shift modifier is dropped before your program ever reads the input, so your TUI can't tell the two apart. tmux sits between the terminal and your app and normalizes keys again, which adds a second place where Shift can get lost.

## Option 1: Turn on extended key reporting

Your app has to ask the terminal for richer key codes. With that enabled, Shift+Enter arrives as a distinct sequence:

| Protocol | Enable (app writes) | Shift+Enter arrives as |
|---|---|---|
| kitty keyboard protocol | `\x1b[>1u` (disable: `\x1b[<u`) | `\x1b[13;2u` |
| xterm modifyOtherKeys | `\x1b[>4;2m` (disable: `\x1b[>4;0m`) | `\x1b[27;2;13~` |

Your parser should treat either sequence as "insert newline". Always disable the mode on exit, or the user's shell will be left in a broken state.

**The outer terminal has to support it:** kitty, WezTerm, Ghostty, foot and Alacritty do. iTerm2 does once you enable *Settings → Profiles → Keys → "Report keys using CSI u"*. macOS Terminal.app doesn't support it.

**tmux needs extra config** (3.2+, ideally 3.5+):

```tmux
set -s extended-keys on            # or "always" to force it
set -as terminal-features 'xterm*:extkeys'
set -s extended-keys-format csi-u  # tmux 3.5+: emit \e[13;2u instead of \e[27;2;13~
```

Then run `tmux kill-server` and start it again, because the server-level options don't reload cleanly. tmux only passes through the modifyOtherKeys / CSI-u *format*, not the full kitty protocol. So inside tmux, request modifyOtherKeys (`\x1b[>4;2m`) and accept both sequence formats.

## Option 2: Fallback keys that work everywhere

Even with Option 1, you should support these, because many users run terminals you can't configure:

- **Ctrl+J** sends `\n` (0x0A), while Enter sends `\r`. It's distinct with no setup, including inside tmux.
- **Alt/Option+Enter** sends `\x1b\r`. This is reliable, but on macOS the user may need to set "Option as Meta" in their terminal.
- **`\` then Enter**: if the character before the cursor is a backslash, replace it with a newline instead of submitting. This is a common convention and needs no terminal support.

## Recommended approach

1. Bind Ctrl+J, Alt+Enter and Shift+Enter (both extended sequences) to "insert newline".
2. Request modifyOtherKeys on startup and turn it off on exit.
3. Show a hint in the input area such as `Ctrl+J / Alt+Enter for newline`, so the user isn't stuck if Shift+Enter can't get through.
4. Enable bracketed paste (`\x1b[?2004h`) so pasted multi-line text is inserted, not submitted line by line.

If you tell me which language or TUI library you're using (Bubble Tea, Ratatui, Ink, Textual, etc.), I can show you the exact key-handling code.
