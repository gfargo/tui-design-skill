# Don't show the spinner right away. Wait about 150–250ms first.

If most runs finish in under 50ms, a spinner that starts immediately will just flash for a frame or two on almost every run. That flicker looks like a glitch, and it makes the fast case feel slower. Here's a better approach:

1. **Start work and a timer together.** Show the spinner only if the work is still running after about 200ms. Below roughly 100ms people perceive a result as instant. 150–250ms gives your 50ms common case plenty of room, while slow runs still get feedback well within the first second.
2. **Optional: once the spinner appears, keep it up for at least ~300ms.** This stops a spinner that appears at 210ms and vanishes at 230ms. It's less important for a one-shot CLI than for a GUI, so skip it if it complicates things.
3. **When the work finishes, erase the spinner line completely** (`\r\x1b[2K`) before printing results. The user should see either clean output or a final status line, never a leftover spinner frame.

## Frames

The standard set is `dots` from cli-spinners (used by ora, and many Go and Rust spinner libraries also ship it):

```
⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏      interval: 80ms
```

If you want something heavier and more visible, use `dots2`:

```
⣾ ⣽ ⣻ ⢿ ⡿ ⣟ ⣯ ⣷      interval: 80ms
```

Keep the interval at 80–100ms. Slower than that looks laggy, and faster burns CPU and looks frantic.

## Other things to get right

- **Write to stderr, not stdout**, so `mytool | jq` still works.
- **Only animate when stderr is a TTY.** Don't animate when `CI` is set or `TERM=dumb`. In those cases print nothing, or one static "Working…" line if the wait is long.
- **Have a fallback for terminals without Braille.** On a non-UTF-8 locale or a legacy Windows console, use `| / - \`.
- **Hide the cursor while spinning (`\x1b[?25l`) and always restore it (`\x1b[?25h`).** That includes Ctrl-C, so handle SIGINT/SIGTERM and clean up before exiting.
- **Put a short label next to the spinner** (`⠹ Resolving dependencies…`) so the slow case explains what it's waiting on.

## Sketch (Node-style)

```js
const frames = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏'];
let i = 0, tick;
const show = setTimeout(() => {
  process.stderr.write('\x1b[?25l');
  tick = setInterval(() => {
    process.stderr.write(`\r${frames[i++ % frames.length]} Working…`);
  }, 80);
}, 200);

try {
  await doWork();
} finally {
  clearTimeout(show);
  if (tick) { clearInterval(tick); process.stderr.write('\r\x1b[2K\x1b[?25h'); }
}
```

With this, the fast path prints nothing extra and the slow path gets a spinner after 200ms.
