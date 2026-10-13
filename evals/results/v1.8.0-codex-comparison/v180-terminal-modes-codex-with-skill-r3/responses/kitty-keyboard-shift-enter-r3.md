**Keep Enter to send, but make Shift+Enter an optional shortcut. Always provide a legacy newline binding, such as Ctrl+J.**

The failure happens before your app’s key handler. Traditional terminal input often encodes both Enter and Shift+Enter as the same carriage-return byte (`0x0d`). Once that happens, Bubble Tea cannot recover the Shift modifier.

Kitty’s keyboard protocol preserves that distinction. Bubble Tea v2 enables keyboard disambiguation and also supports `modifyOtherKeys`, but the entire input path must cooperate. tmux is another terminal layer: its version, configuration, and outer terminal determine whether modified keys survive. A supporting outer terminal alone is insufficient.

The recommended composer contract is:

| Input | Action |
|---|---|
| Enter | Send |
| Ctrl+J | Insert newline |
| Shift+Enter, when distinguishable | Insert newline |
| Bracketed multiline paste | Insert text, never send |

Ctrl+J normally sends line feed (`0x0a`), distinct from Enter’s carriage return in raw mode. **Ctrl+Enter is not a reliable fallback**; it can collapse to Enter too.

For Bubble Tea v2:

- Handle `tea.KeyPressMsg`, checking `"shift+enter"` and `"ctrl+j"` for newline and `"enter"` for send.
- Consume send events before forwarding input to the textarea. Configure the textarea’s newline bindings to match your contract.
- Keep paste handling separate from submit handling; pasted newlines must remain draft content.
- Let Bubble Tea manage keyboard negotiation and cleanup. Do not infer support solely from `$TERM`, `$TMUX`, or the terminal’s name.

Show a stable composer hint: `Enter send · Ctrl+J newline`. Add Shift+Enter to help when support is established. Missing or unanswered capability queries should leave the fallback usable immediately.

For tmux users, document `set -s extended-keys on` and any version-specific outer-terminal `extkeys` configuration needed. This is an optional enhancement; users should not need to configure tmux to compose multiline messages.

If accidental submission is particularly costly, offer an explicit, persistent compose mode: **Enter inserts newline; Ctrl+S or a keyboard-focusable Send control submits.** Avoid silently changing Enter’s meaning as capability replies arrive.

Verify synthetic update events for send, newline, and paste, then test actual keys directly in kitty, in a legacy terminal, and through tmux with extended keys off and on. Log decoded events to a file.

For the layout, one compact hint line is enough—no extra bordered compatibility panel. At 80×24 and in a 60-column tmux split, preserve the composer and essential hints; shorten conversation chrome first.