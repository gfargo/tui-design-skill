Keep **Enter to send**, and provide a newline shortcut that works with legacy terminal input.

| Key | Action |
|---|---|
| Enter | Send |
| Ctrl+J | Insert newline |
| Alt+Enter | Insert newline, where available |
| Shift+Enter | Optional newline shortcut when distinguishable |
| `\` then Enter | Remove the trailing `\` and insert a newline |

Many terminals encode **Enter and Shift+Enter identically**, so your app cannot distinguish them. Negotiate an enhanced keyboard protocol, such as Kitty’s, through your framework; keep the fallback bindings even when negotiation succeeds. tmux and other intermediate layers can limit what reaches your app.

For implementation:

- Preserve the distinction between carriage return (`Enter`) and line feed (`Ctrl+J`) in legacy input.
- Enable **bracketed paste**: pasted newlines belong in the draft and must never trigger sending.
- Show a persistent hint: `Enter send · Ctrl+J newline`.
- Test ordinary terminal input, tmux, and multiline paste.

The composer can use the same compact layout at 80 and 60 columns:

```text
Wide                              60-column split
Message:                          Message:
> Draft text                      > Draft text
Enter send · Ctrl+J newline        Enter send · Ctrl+J newline
```

One hint line is sufficient; avoid adding a separate warning or extra border for keyboard compatibility.