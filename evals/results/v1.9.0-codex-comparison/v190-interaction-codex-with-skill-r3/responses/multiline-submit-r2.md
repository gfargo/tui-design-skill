Keep **Enter to send**, and provide a newline binding that works with legacy terminal input:

| Key | Action |
|---|---|
| Enter | Send |
| Ctrl+J | Insert newline |
| Alt+Enter | Insert newline, where available |
| Shift+Enter | Insert newline when extended keyboard support is negotiated |
| Trailing `\` then Enter | Remove that `\` and insert newline as a fallback |

In many terminals, **Shift+Enter sends exactly the same bytes as Enter**. Your app cannot distinguish them. The Kitty keyboard protocol can make them distinct, but terminals and multiplexers must support and forward it; tmux’s extended keys are off by default. Use your framework’s protocol support, with a bounded capability query and proper cleanup.

Implementation details that matter:

- Preserve **CR (`\r`, Enter)** versus **LF (`\n`, Ctrl+J)** in your input handling; don’t normalize them before dispatch.
- Enable **bracketed paste**. Pasted newlines should enter the draft and **never send it**.
- Show the reliable binding beside the composer: `Enter send · Ctrl+J newline`. Put additional bindings in help.
- Test directly and inside tmux, including a multiline paste.

Keep the hint on one line at both 80 and 60 columns; no extra panel or border is needed. Shift+Enter can be a convenient shortcut, but it shouldn’t be the only way to write multiple lines.