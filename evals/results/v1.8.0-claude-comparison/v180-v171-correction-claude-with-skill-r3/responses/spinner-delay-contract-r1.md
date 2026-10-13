**No, don't show it the instant work starts.** Wait about 100–200ms, then start the spinner. In your case most runs finish in under 50ms, so those runs never show a spinner. A spinner that appears and vanishes within one or two frames looks twitchy. Slow runs get a spinner well before the silence starts to feel like a hang, which happens after a few hundred milliseconds. (Sources: `references/visual-patterns.md` → *Spinners*, and `references/cli-basics.md` → *Progress*.)

**Frames:** use the 10-frame Braille "dots" set from cli-spinners, at about 80ms per frame:

```
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
```

**Rules that go with it:**
- **Write it to stderr**, not stdout, so piped output stays clean.
- **Don't animate when output isn't a TTY.** CI logs and pipes should get no spinner.
- **End with a final state:** `✓` for success, `✗` for failure, or just clear the line. Fast runs that never showed a spinner just print their result as usual.
- **Offer a static mode.** In plain, screen-reader or reduced-motion mode, print one line like `Fetching…` instead of animating.

A sketch of the pattern:

```js
const frames = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏'];
let i = 0, timer, delay;

if (process.stderr.isTTY) {
  delay = setTimeout(() => {
    timer = setInterval(() => {
      process.stderr.write(`\r${frames[i++ % frames.length]} Working…`);
    }, 80);
  }, 150);
}

try {
  await doWork();
} finally {
  clearTimeout(delay);
  if (timer) { clearInterval(timer); process.stderr.write('\r\x1b[2K'); } // then print ✓/✗ line if you like
}
```

If the slow path sometimes takes many seconds and you can measure progress, switch to a determinate progress bar for that part.
