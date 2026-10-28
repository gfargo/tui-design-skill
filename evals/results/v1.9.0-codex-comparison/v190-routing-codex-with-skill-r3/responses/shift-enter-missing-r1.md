**Try Alt+Enter or Ctrl+J**—provided your app binds one to “insert newline.” Some apps also support typing `\` followed by Enter.

In legacy terminal encoding, **Shift+Enter and Enter often send the same carriage-return byte**. Your TUI cannot distinguish them. Ctrl+J sends a separate line-feed byte, making it a useful fallback.

If you’re implementing the input field:

- Bind **Enter → submit**, **Alt+Enter / Ctrl+J → newline**.
- Show a compact hint: `Enter send · Alt+Enter newline`.
- Support Shift+Enter through an enhanced keyboard protocol, such as Kitty keyboard, but keep the fallback.
- Enable bracketed paste so pasted newlines insert text without submitting.

For tmux, enable extended keys in `~/.tmux.conf` on versions that support it:

```tmux
set -s extended-keys on
```

Reload with:

```sh
tmux source-file ~/.tmux.conf
```

The terminal, tmux, and app must all support the enhanced key encoding; that setting alone cannot guarantee Shift+Enter works. Test the app outside tmux first: if Shift+Enter works there, tmux is where to investigate next.