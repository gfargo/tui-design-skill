**Try `Alt+Enter` or `Ctrl+J`**, if your TUI binds either to newline. Some apps also support typing `\` followed by Enter. These are app conventions, not universal shortcuts.

Legacy terminals often send **the same carriage-return byte for Enter and Shift+Enter**. Once that happens, the app cannot distinguish them. tmux can also prevent extended key information from reaching the app.

If you’re implementing the input field:

- Bind `Alt+Enter` and/or `Ctrl+J` to insert `\n`. In legacy encoding, Ctrl+J sends LF; Enter normally sends CR. Preserve that distinction in your input decoder.
- Support Shift+Enter through negotiated **Kitty keyboard protocol** or supported `modifyOtherKeys`, with a legacy fallback.
- For compatible tmux versions, enable extended keys in `~/.tmux.conf`:
  ```tmux
  set -s extended-keys on
  ```
  Reload the configuration and restart the TUI. The outer terminal, tmux, and app must all support the path; this setting alone cannot guarantee Shift+Enter works.
- Enable bracketed paste so pasted multiline text inserts newlines without submitting.

Make the working shortcut visible: `Enter send · Alt+Enter newline`. For an editor-style field, prefer Enter inserting a newline and a separate send/save action.