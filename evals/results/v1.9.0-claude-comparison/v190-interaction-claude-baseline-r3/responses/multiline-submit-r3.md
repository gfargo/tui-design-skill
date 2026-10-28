The terminal is usually the problem, not your code. In the classic terminal protocol, Enter and Shift+Enter send the same byte (`\r`), so your app can't tell them apart. Some terminals can report Shift+Enter, but you have to turn that on, and many terminals can't do it at all. The usual fix is to support Shift+Enter where it's available and give users fallbacks that work everywhere.

## 1. Turn on enhanced key reporting where it's supported

**Kitty keyboard protocol (CSI u).** Supported by Kitty, WezTerm, Ghostty, foot, recent Alacritty, and iTerm2 (after enabling it in settings).

```
on start:  write "\x1b[>1u"    # push "disambiguate" mode
on exit:   write "\x1b[<u"     # pop it (also on crash/SIGINT!)
```

Once that's on, Shift+Enter arrives as `\x1b[13;2u` and plain Enter is still `\r`.

You can check whether the terminal supports it by sending `\x1b[?u` followed by `\x1b[c`. If a `\x1b[?…u` reply comes back before the DA1 reply, the protocol is supported.

**xterm modifyOtherKeys.** The older alternative: `\x1b[>4;2m` to enable, `\x1b[>4m` to disable. Shift+Enter then arrives as `\x1b[27;2;13~`.

**tmux** removes these sequences unless the user has `set -g extended-keys on` (plus `extended-keys-format csi-u` on tmux 3.5+). Put that in your docs.

**macOS Terminal.app** supports neither, so it needs the fallbacks below.

## 2. Add fallbacks that work in every terminal

Accept all of these as "insert newline":

| Key | Bytes received | Notes |
|---|---|---|
| **Ctrl+J** | `\n` | Works almost everywhere. In raw mode with `ICRNL` off, Enter is `\r`, so the two are distinct. |
| **Alt/Option+Enter** | `\x1b\r` | On macOS this only works if "Use Option as Meta" is enabled. |
| **`\` then Enter** | `\\` + `\r` | If the character before the cursor is `\`, replace it with a newline instead of sending. This works in every terminal. |

A sketch of the key handling:

```python
def on_key(seq):
    if seq in ("\x1b[13;2u", "\x1b[27;2;13~",   # Shift+Enter (CSI u / modifyOtherKeys)
               "\n",                             # Ctrl+J
               "\x1b\r"):                        # Alt+Enter
        insert("\n")
    elif seq == "\r":
        if buffer_before_cursor().endswith("\\"):
            delete_back(1); insert("\n")
        else:
            submit()
```

## 3. Related things that are easy to miss

- **Bracketed paste** (`\x1b[?2004h`): turn this on so a pasted block of text with newlines gets inserted instead of sending each line. Anything between `\x1b[200~` and `\x1b[201~` should be treated as literal text.
- **Restore the terminal on exit.** Pop the keyboard mode, turn off bracketed paste, and restore termios in every exit path, including signals. If you don't, the user's shell is left in a broken state.
- **Tell users how to do it.** Put a short hint near the input, like `Enter to send · Shift+Enter / Ctrl+J for newline`. If you detected that CSI u isn't supported, show `\⏎` or `Ctrl+J` instead of Shift+Enter.
- **Open an external editor:** optionally, bind Ctrl+G or Ctrl+X Ctrl+E to open `$EDITOR` for writing longer messages.

If you're using a TUI library (Bubble Tea, Textual, Ink, ratatui/crossterm, etc.), check whether it already handles the kitty protocol. crossterm has `PushKeyboardEnhancementFlags`, and recent Bubble Tea and Textual versions support it. Using the library's support is better than parsing the bytes yourself. Tell me which stack you're on and I can show the exact setup.
