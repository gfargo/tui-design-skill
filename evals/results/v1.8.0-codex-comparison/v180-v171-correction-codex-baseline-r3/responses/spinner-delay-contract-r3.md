No—delay the spinner by about **150–200ms**. Since most runs finish under 50ms, showing it immediately creates a distracting flash. If work is still running after the delay, show it and animate every **80–100ms**.

Use the standard 10-frame Braille sequence:

```text
⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
```

For a one-shot CLI:

- Write the spinner to **stderr**, only when stderr is a TTY.
- Clear it when work finishes, then print the normal result.
- Disable animation for redirected output or unsupported terminals.
- For multi-second runs, pair it with a short label such as `Fetching…`.

That keeps fast commands quiet and gives slower runs a clear sign of activity.