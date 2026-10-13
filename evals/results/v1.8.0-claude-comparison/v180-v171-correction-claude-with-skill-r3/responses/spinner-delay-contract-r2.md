**No, don't show it right away.** Start the work, wait about 100–200 ms, and only show the spinner if the work is still running. Your usual runs finish in under 50 ms, so they'll never show a spinner. The slow runs will show one well before the pause starts to feel like a hang. If the spinner appears instantly, the common fast case flashes one frame, which looks twitchy.

**Frames:** use the 10-frame Braille `dots` set from cli-spinners. It's the usual modern default:

```
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
```

Advance one frame about every 80 ms, which gives a smooth rotation.

**Other rules to follow:**

- **Write the spinner to stderr, never stdout.** That keeps piped output clean.
- **Only animate when stderr is a TTY.** In CI, pipes or `TERM=dumb`, show no spinner at all.
- **End on a final state:** replace the spinner with `✓ Done`, `✗ Failed: …`, or just clear the line. Don't leave a frozen frame on screen.
- **Give users an off switch.** Provide a reduced-motion or plain mode through a flag or env var, like gh's `GH_SPINNER_DISABLED`. In that mode, print one static `Working…` line and then the final status.
- **Use an ASCII fallback** such as `| / - \` if you can't be sure the terminal renders Unicode.

**Implementation sketch** (works in any language):

```
start work
timer = after(150ms): if still running and stderr is TTY → start spinner (80ms ticks)
on finish: cancel timer; if spinner shown → clear line, print ✓/✗ to stderr
print result to stdout
```

If you're in Rust, `indicatif` already hides itself on non-TTY output. In Node, `ora` ships the `dots` frames. In Go, Bubbles' `spinner.Dot` is Braille. With all three, you add the delay yourself by starting the spinner from the timer rather than at launch.
