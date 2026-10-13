Don’t show the spinner immediately. Delay it by **150–200ms** so typical runs finish without flashing anything. If work is still running, show it; clear it when done.

Use this standard Braille sequence at **80–100ms per frame**:

```text
⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
```

Write it to **stderr**, and animate only when stderr is a TTY. For redirected output or CI, omit animation. If Unicode support is uncertain, fall back to `| / - \`.

For a one-shot CLI, don’t enforce a minimum spinner duration—it would slow down completion just to preserve the animation.