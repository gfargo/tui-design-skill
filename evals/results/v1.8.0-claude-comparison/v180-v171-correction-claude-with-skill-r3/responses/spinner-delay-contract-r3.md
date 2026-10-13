**No, don't show it right away.** Wait about 100–200ms before you show the spinner. Most of your runs finish in under 50ms, so those will never show a spinner at all. If a spinner appears and vanishes almost instantly, it looks twitchy. But if the screen stays blank for more than a few hundred milliseconds, the CLI looks frozen. So your slow runs need the spinner, and they'll get it after the delay.

**Frames:** use the 10-frame Braille "dots" set from `cli-spinners`, at about 80ms per frame:

```
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
```

**Rules that go with it:**
- **Write the spinner to stderr**, not stdout, so it doesn't end up in piped output.
- **Only animate on a TTY.** If stderr isn't a terminal (CI, redirected output), don't draw a spinner at all.
- **End with a final state:** replace the spinner with `✓` for success or `✗` for failure, or just clear the line. Don't leave a stale frame behind.
- **Plain, screen-reader or reduced-motion mode:** print one static line, such as `Working…`, instead of animating.

**How to do it:** start a timer when the work begins. If the work finishes before the timer fires, cancel the timer and nothing is ever drawn. If the timer fires first, start the spinner.

```ts
const show = process.stderr.isTTY
  ? setTimeout(() => spinner.start(), 150)
  : undefined;
try {
  await work();
  clearTimeout(show);
  if (spinner.isSpinning) spinner.succeed('Done');   // ✓
} catch (err) {
  clearTimeout(show);
  if (spinner.isSpinning) spinner.fail('Failed');    // ✗
  throw err;
}
```

Most spinner libraries (ora, Go's spinner packages, indicatif) don't add this delay for you, so you have to write it yourself as above.

This comes from the skill's `references/visual-patterns.md:556` (*Spinners*) and `references/cli-basics.md:105`.
