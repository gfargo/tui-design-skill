The directory is empty, so I can't see your code. This answer is about the general problem, not your specific code.

## Why it happens

By default, terminals send the same byte (`\r`, 0x0D) for both Enter and Shift+Enter. Your app can't tell them apart because the terminal never sends anything different. tmux makes it worse: even if your outer terminal sends a distinct sequence, tmux re-encodes keys and drops modifiers unless you tell it not to.

## Fix, in order of reliability

### 1. Accept keys that work in every terminal

Support these regardless of anything else:

| Key | Bytes received | Works in tmux? |
|---|---|---|
| **Ctrl+J** | `\n` (0x0A) | Yes |
| **Alt/Option+Enter** | `\x1b\r` | Yes (needs "Option as Meta" on macOS) |

Ctrl+J only stays distinct if raw mode turns off `ICRNL`. Most raw-mode libraries do this already. If `ICRNL` is on, the terminal driver converts Enter's `\r` into `\n` and the two keys look identical.

### 2. Turn on extended key reporting

This makes Shift+Enter send its own sequence. When your app starts, write:

```
\x1b[>4;2m     # xterm modifyOtherKeys level 2
\x1b[>1u       # kitty keyboard protocol (disambiguate)
```

On exit, undo them with `\x1b[>4;0m` and `\x1b[<u`.

Then treat any of these as "insert newline":

```
\x1b[13;2u       # CSI-u / kitty: Shift+Enter
\x1b[27;2;13~    # modifyOtherKeys: Shift+Enter
\x1b\r           # Alt+Enter
\n               # Ctrl+J
```

### 3. Configure tmux (version 3.2 or later)

tmux won't pass Shift+Enter through without this in `~/.tmux.conf`:

```tmux
set -s extended-keys on            # or 'always' to skip the app request
set -as terminal-features 'xterm*:extkeys'
set -s extended-keys-format csi-u  # tmux 3.5+: emit \x1b[13;2u instead of 27;2;13~
```

Then run `tmux kill-server` (a reload isn't always enough). tmux doesn't fully implement the kitty protocol, but it does handle modifyOtherKeys, which is why you should parse both sequence formats.

### 4. Or remap the key in the terminal emulator

This is a user-side workaround that makes Shift+Enter send `\n`:

- **Ghostty:** `keybind = shift+enter=text:\n`
- **kitty:** `map shift+enter send_text all \n`
- **WezTerm:** `{key="Enter", mods="SHIFT", action=wezterm.action.SendString("\n")}`
- **iTerm2:** Settings → Profiles → Keys → Key Mappings → add Shift+Return → "Send Hex Codes" `0x0a`
- **Terminal.app:** no support for extended keys. Use Option+Enter with "Use Option as Meta key" turned on.

## Recommendation

Always accept Ctrl+J and Alt+Enter, and request the extended modes for Shift+Enter when the terminal supports them. Show a hint in the input area like `Enter send · Ctrl+J / Alt+Enter newline`, so users stuck in plain tmux or Terminal.app still have a way to insert a newline.

If you share your input-handling code or tell me which library you're using (Bubble Tea, Ratatui/crossterm, Ink, Textual…), I can point to the exact changes.
