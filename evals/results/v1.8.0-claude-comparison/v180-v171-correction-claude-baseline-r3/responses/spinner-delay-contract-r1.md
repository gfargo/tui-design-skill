**No. Wait about 100–200 ms before showing it.** If the work finishes within that window, the user never sees a spinner. That's what you want for your common case, which is under 50 ms.

## Why delay

- **Under ~100 ms feels instant.** A spinner that appears and disappears in 40 ms looks like a glitch.
- **Most runs never need it.** Since you usually finish in under 50 ms, starting the spinner immediately means it flickers on almost every run.
- **The slow runs still get feedback.** A 150 ms delay is unnoticeable on a multi-second run.

A simple pattern:

```js
const FRAMES = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏'];
let timer, frame = 0;

const show = setTimeout(() => {
  process.stderr.write('\x1b[?25l');               // hide cursor
  timer = setInterval(() => {
    process.stderr.write(`\r${FRAMES[frame++ % FRAMES.length]} Working…`);
  }, 80);
}, 150);

try {
  await doWork();
} finally {
  clearTimeout(show);
  if (timer) {
    clearInterval(timer);
    process.stderr.write('\r\x1b[K\x1b[?25h');     // clear line, show cursor
  }
}
```

Some UIs also keep a spinner visible for at least ~300 ms once it appears, so it doesn't flash. In a CLI the spinner is replaced by output right away, so you usually don't need that. The delay alone fixes most of the flicker.

## Frames

Use the standard "dots" set (the default in `cli-spinners`/`ora`) at an **80 ms** interval:

```
⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
```

It's widely recognized, looks smooth, and every frame is the same width, so the text after it doesn't shift.

If you want something heavier, this is a good alternative:

```
⣾ ⣽ ⣻ ⢿ ⡿ ⣟ ⣯ ⣷
```

## Other details to get right

- **Write to stderr**, not stdout, so piped output stays clean.
- **Only animate when stderr is a TTY** (`process.stderr.isTTY`), and skip it when `CI` is set. Otherwise logs fill up with `\r` junk.
- **Always restore the cursor**, including on SIGINT, SIGTERM and uncaught errors. A hidden cursor left behind after Ctrl-C is the most common spinner bug.
- **Fall back to ASCII** (`| / - \`) if the locale isn't UTF-8 or you're on an old Windows console.
- **Clear the line** (`\r\x1b[K`) before printing the result, so no spinner remnants are left behind.
