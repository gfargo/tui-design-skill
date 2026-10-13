No—delay the spinner by **100–200ms**; **150ms** is a sensible default. If work finishes first, cancel the timer and show no spinner. This keeps your usual <50ms runs from flashing while giving feedback during slower runs.

Use these ten Braille frames in order, looping at **~80ms per frame** (`cli-spinners`’ `dots`):

```text
⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
```

Render one inline spinner with a short label on **stderr**, only when stderr is a TTY. Clear it on completion or replace it with `✓` / `✗`. Suppress animation in non-TTY output; use a static status line for plain, screen-reader, or reduced-motion modes.