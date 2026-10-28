The problem isn't your code. In most terminals, Enter and Shift+Enter send the exact same byte (`\r`). The old terminal input protocol has no way to say "Shift was held" for Enter, so your app can't tell them apart. Only terminals that support newer keyboard protocols can.

The usual fix is to support several ways of adding a newline, so every user has at least one that works.

## 1. Turn on enhanced keyboard reporting where it's available

**Kitty keyboard protocol.** Supported by Kitty, WezTerm, Ghostty, foot, recent iTerm2 and Alacritty, and Windows Terminal.
- On startup, write `\x1b[>1u`. On exit, write `\x1b[<u`. Always restore it, including on crash or SIGINT.
- Shift+Enter then arrives as `\x1b[13;2u`.
- To detect support: send `\x1b[?u` followed by `\x1b[c`. If a `\x1b[?…u` reply comes back before the DA1 reply, the terminal supports it.

**xterm modifyOtherKeys.** This is a fallback for xterm and some others.
- Turn it on with `\x1b[>4;2m` and off with `\x1b[>4;0m`.
- Shift+Enter then arrives as `\x1b[27;2;13~`.

**tmux** strips these sequences unless the user sets `set -g extended-keys on`. If you can, say so in your docs.

**macOS Terminal.app** supports neither protocol. Shift+Enter will never work there, so you need the fallbacks below.

## 2. Add fallbacks that work in every terminal

| Key | Bytes | Notes |
|---|---|---|
| **Ctrl+J** | `\n` (0x0A) | Works everywhere. In raw mode Enter is `\r` and Ctrl+J is `\n`, so they're distinct. Check that your TUI library doesn't merge both into "enter". |
| **Alt/Option+Enter** | `\x1b\r` | Works in most terminals. On macOS the user has to enable "Use Option as Meta". |
| **`\` then Enter** | `\\` + `\r` | If the character before the cursor is `\`, replace it with a newline instead of sending. People find this one without being told, and it works everywhere. |

## 3. Turn on bracketed paste

Without it, pasting multi-line text sends the message at the first newline. Turn it on with `\x1b[?2004h`. Pasted text then arrives wrapped in `\x1b[200~ … \x1b[201~`. Insert everything between those markers as literal text.

## Sketch of the input handling

```ts
function handleKey(seq: string) {
  switch (seq) {
    case "\r":
      if (buffer.charBefore(cursor) === "\\") {
        buffer.deleteBack(); buffer.insert("\n");
      } else {
        submit();
      }
      return;
    case "\n":              // Ctrl+J
    case "\x1b\r":          // Alt+Enter
    case "\x1b[13;2u":      // Shift+Enter (kitty)
    case "\x1b[27;2;13~":   // Shift+Enter (modifyOtherKeys)
      buffer.insert("\n");
      return;
  }
  // ...other keys
}
```

A lone `\x1b` could be the Esc key or the start of Alt+Enter. Handle it with a short timeout (about 25–50 ms) before treating it as Esc.

## 4. Tell users how

Show a hint near the input, such as `Enter to send · Ctrl+J or \ + Enter for newline`. If you detected kitty or modifyOtherKeys support, you can show "Shift+Enter" instead.

If you tell me your language or TUI library (Ink, Bubble Tea, Textual, ratatui, etc.), I can show you how to do this with it. Several of them already parse these sequences, or have options to turn the protocols on.
