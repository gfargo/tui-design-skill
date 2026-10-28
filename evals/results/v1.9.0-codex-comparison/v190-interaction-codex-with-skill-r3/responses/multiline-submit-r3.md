Keep **Enter to send**, and give newline insertion several paths:

| Key | Action |
|---|---|
| Enter | Send |
| Alt+Enter or Ctrl+J | Insert newline |
| Shift+Enter | Insert newline when supported |
| Trailing `\` then Enter | Remove that `\` and insert newline |

Legacy terminals often encode **Shift+Enter exactly like Enter**. Your app cannot distinguish identical input. Negotiate the Kitty keyboard protocol through your framework to recognize it where supported, but retain the fallback bindings—especially through tmux and SSH. Ctrl+J normally sends line feed (`LF`), distinct from Enter’s carriage return (`CR`); ensure your input layer preserves that distinction.

Also enable **bracketed paste**: pasted newlines must enter the draft and **never trigger sending**.

Keep the controls visible in one compact footer, at both 80×24 and a 60-column split:

```text
> Draft message…
Enter send · Alt+Enter newline
```

Put Ctrl+J and the `\` fallback in help. Avoid adding a separate bordered instructions panel.

Verify Enter, each newline route, and multiline paste in a legacy terminal, a protocol-capable terminal, and inside tmux. Restore any keyboard and paste modes your app enables on exit.