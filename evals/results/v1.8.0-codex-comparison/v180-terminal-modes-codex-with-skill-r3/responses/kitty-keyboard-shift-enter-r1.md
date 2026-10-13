**Keep Enter to send, but make Ctrl+J the always-available newline binding. Treat Shift+Enter as an optional accelerator.**

Legacy terminal input often encodes both Enter and Shift+Enter as the same carriage-return byte (`0x0d`). Once that happens, Bubble Tea cannot recover the Shift modifier. This is information lost before your app receives the event.

Kitty’s keyboard protocol distinguishes them. Bubble Tea v2 enables keyboard enhancements, including Kitty disambiguation and `modifyOtherKeys`, but support must survive the whole path:

`terminal → tmux → Bubble Tea`

Tmux can translate or discard extended key information; its version, `extended-keys` setting, and outer-terminal support matter. Working directly in kitty does not guarantee working inside tmux. Neither `$TERM` nor `$TMUX` proves that Shift+Enter arrives distinctly.

Use this input contract:

| Input | Action |
|---|---|
| Enter | Send |
| Ctrl+J | Insert newline |
| Shift+Enter, when received distinctly | Insert newline |
| Bracketed paste, including newlines | Insert text; never send |

Ctrl+J has a separate legacy encoding—line feed (`0x0a`)—so it avoids the Shift+Enter collision. **Ctrl+Enter has the same portability problem as Shift+Enter** and should not be the fallback.

In Bubble Tea v2, handle `tea.KeyPressMsg`, match the complete key including modifiers, and consume send events before forwarding input to the textarea. Configure the textarea’s newline bindings explicitly. Keep paste handling separate from submission, and let Bubble Tea manage protocol setup and cleanup.

Show one compact footer:

```text
Enter send · Ctrl+J newline
```

Add Shift+Enter to help when supported, without replacing Ctrl+J. Offer an explicit multiline preference—Enter inserts newline, Ctrl+S sends—for users who want protection against accidental sends. Keep that preference stable across sessions rather than silently changing Enter’s meaning based on capability detection.

For this composer, use one hint row and avoid nested borders or repeated instructions. At 80×24 and in a 60-column tmux split, preserve the composer and send/newline hints; hide secondary panes first.

Verify actual decoded events directly and inside tmux, using file logging rather than terminal output. Test distinct Shift+Enter, collapsed Enter, Ctrl+J, and multiline paste. **Synthetic key tests verify your handler; real terminal tests verify whether the modifier reaches it.**