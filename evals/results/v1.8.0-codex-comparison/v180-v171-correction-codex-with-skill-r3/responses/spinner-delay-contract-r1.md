No—delay the spinner by **100–200ms**; **150ms** is a good default. If work finishes before then, cancel it without rendering anything. This avoids flashing on the usual sub-50ms runs while giving feedback on slower ones.

Use these ten Braille frames, advancing every **~80ms**:

```text
⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
```

Write the spinner to **stderr**, keeping stdout for results. On completion, clear it or replace it with `✓` / `✗` and a short message. Suppress animation when stderr isn’t a TTY; use a static status line in plain, screen-reader, or reduced-motion mode.