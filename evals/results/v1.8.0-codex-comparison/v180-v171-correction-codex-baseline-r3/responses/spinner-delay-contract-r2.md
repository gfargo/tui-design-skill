No. For a CLI that usually finishes in under 50 ms, an immediate spinner creates distracting flashes. Delay it by **150–200 ms**, and cancel the timer if work finishes first. Once visible, animate every **80–100 ms**. Don’t delay completion just to keep the spinner on screen.

A familiar Braille sequence is:

```text
⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
```

Show it only on an interactive terminal, hide it in quiet mode, and clear its line when work finishes. Use a simple ASCII sequence such as `| / - \` if Unicode rendering is unreliable.