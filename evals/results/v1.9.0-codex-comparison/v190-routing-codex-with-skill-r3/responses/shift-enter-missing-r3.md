Try **Alt+Enter** or **Ctrl+J** if your app binds either to newline. Some apps also support typing `\` followed by Enter. These are app bindings, so they aren’t guaranteed.

In traditional terminal encoding, **Shift+Enter and Enter often send the same carriage-return byte**. Your TUI cannot distinguish them. Ctrl+J sends a distinct line-feed byte, provided the input layer preserves that distinction.

If you’re implementing the field:

- Bind **Enter → submit**, **Alt+Enter or Ctrl+J → newline**.
- Show a hint: `Enter send · Alt+Enter newline`.
- Enable bracketed paste so pasted newlines insert text without submitting.
- Support Shift+Enter through an enhanced keyboard protocol, such as Kitty’s, while retaining a fallback.

Inside tmux, extended keys are off by default. On a supporting tmux version, add this to `~/.tmux.conf` and reload it:

```tmux
set -s extended-keys on
```

The outer terminal, tmux, and your app’s input library must all support the encoding. Compare behavior outside and inside tmux: if Shift+Enter works only outside, check tmux’s extended-key support and terminal detection. Enabling tmux alone won’t create a newline binding in the app.