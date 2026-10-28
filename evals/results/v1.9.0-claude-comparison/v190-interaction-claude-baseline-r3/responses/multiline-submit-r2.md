The working directory has no source files, so this answer isn't tied to your framework. Send me your input-handling code if you want specific changes.

## Why Shift+Enter fails

In a traditional terminal, Enter and Shift+Enter both send the same byte, `\r`. The terminal drops the Shift before your app sees it, so no amount of app code can tell them apart. The only fix is an extended keyboard protocol, and not every terminal supports one. macOS Terminal.app doesn't, and tmux/screen often strip it unless configured.

## Recommended approach: layer several methods

### 1. Turn on extended keys where the terminal supports them
At startup, write these sequences and undo them on exit, including on crash or SIGINT:

```
\x1b[>1u      # kitty keyboard protocol (disambiguate) — kitty, WezTerm, Ghostty, foot, Alacritty, recent iTerm2
\x1b[>4;2m    # xterm modifyOtherKeys — xterm and some others
```
On exit, send `\x1b[<u` and `\x1b[>4;0m`.

Shift+Enter then arrives as one of:
- `\x1b[13;2u` (kitty/CSI u)
- `\x1b[27;2;13~` (modifyOtherKeys)

To detect support, send `\x1b[?u` followed by `\x1b[c`. If a `\x1b[?…u` reply comes back before the DA1 reply, the kitty protocol is available.

tmux users need `set -s extended-keys on` (plus `extended-keys-format csi-u` on tmux 3.5+).

### 2. Always accept fallbacks that work everywhere
| Key | Bytes | Notes |
|---|---|---|
| **Alt/Option+Enter** | `\x1b\r` | Works almost everywhere. On macOS, Option must be set to act as Meta (Terminal.app: Settings → Profiles → Keyboard). |
| **Ctrl+J** | `\n` | Works in every terminal. In raw mode Enter is `\r` and Ctrl+J is `\n`, so they're distinct. |
| **`\` then Enter** | — | If the character before the cursor is `\`, replace it with a newline instead of sending. No configuration needed and easy to discover. |

### 3. Enable bracketed paste
Send `\x1b[?2004h`. Pasted text then arrives wrapped in `\x1b[200~ … \x1b[201~`. Insert it as-is so newlines inside a paste never trigger a send. Many "it sent my message halfway through" bugs come from skipping this.

### 4. Tell users
Show a hint near the input such as `Enter to send · Shift+Enter / Alt+Enter / Ctrl+J for newline`. If you detected that extended keys aren't available, mention only the methods that will work. Some apps also include a setup command that adds a terminal keybinding mapping Shift+Enter to `\x1b\r`, for example in iTerm2, VS Code, or Terminal.app.

## Example key handler
```ts
const NEWLINE_SEQS = new Set([
  "\x1b[13;2u",     // Shift+Enter (kitty / CSI u)
  "\x1b[27;2;13~",  // Shift+Enter (modifyOtherKeys)
  "\x1b\r",         // Alt+Enter
  "\n",             // Ctrl+J (some terminals also send this for Ctrl/Shift+Enter)
]);

function onKey(seq: string) {
  if (inPaste) return insert(seq);          // bracketed paste: never submit
  if (NEWLINE_SEQS.has(seq)) return insert("\n");
  if (seq === "\r" || seq === "\x1b[13u") {
    if (charBeforeCursor() === "\\") { deleteBack(); return insert("\n"); }
    return submit();
  }
  // ...
}
```

Your input parser needs to treat each of these escape sequences as a single token, so `\x1b\r` isn't split into Esc followed by Enter. If you use a library, check what it does first. Ink, Bubble Tea, Textual, crossterm and ratatui each handle some of this. For example, crossterm exposes `PushKeyboardEnhancementFlags`, and Bubble Tea v2 supports the kitty protocol.

Tell me which language or framework you're using and I can make this specific to it.
