No—delay the spinner by **100–200ms**; **150ms** is a good default. Cancel its pending appearance if work finishes first, so your usual sub-50ms runs produce no flicker.

Use the standard ten-frame Braille `dots` sequence, advancing every **80ms**:

```text
⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
```

Write it to **stderr**, and animate only when stderr is a TTY. On completion, clear it or replace it with a final status. For plain, screen-reader, or reduced-motion mode, use one static status line instead.