I didn't find any code in the working directory, so this is a general design rather than a review of your implementation. Each of the three symptoms has a different cause and a standard fix.

## 1. Stalls over SSH: don't wait on a timer

The usual cause is code that sends the background-color query (OSC 11) and then blocks on a read with a timeout. If the terminal doesn't support the query, you wait out the whole timeout. Over SSH, a short timeout can also expire before a real answer gets back.

**Fix: send a second query right after it as a sentinel.** Primary Device Attributes (`ESC [ c`) is answered by almost every terminal. Replies come back in order, so:

```
write: ESC ] 11 ; ? ESC \     # what's your background?
write: ESC [ c                # DA1: sentinel
```

- If the OSC 11 reply (`ESC ] 11 ; rgb:RRRR/GGGG/BBBB ESC \` or ending in BEL) arrives before the DA1 reply, use it.
- If the DA1 reply (`ESC [ ? … c`) arrives first, the terminal doesn't support OSC 11. You know right away, with no timer and no guessing about latency.

Keep a long safety timeout (1–2 s) only for the rare setup that answers nothing at all, such as a broken multiplexer or a pipe pretending to be a TTY.

**Don't block the first frame on the answer either:**
- Render immediately with a best guess: a user override, then `COLORFGBG`, then dark as the default.
- Re-theme when the reply arrives. One repaint is cheaper than a visible pause.
- Parse the replies in your normal input decoder, not in a separate pre-startup read. Otherwise a late reply leaks into the input as junk keystrokes like `]11;rgb:1e1e/...`, and a separate read can also swallow keys the user typed early.

## 2. Terminals that never answer: a fallback chain

Resolve the theme in this order and stop at the first hit:

1. **Explicit user choice:** a `--theme=light|dark|auto` flag, a config entry, or an environment variable like `MYAPP_THEME`. This is the escape hatch for every case detection gets wrong. Make it easy to find.
2. **The terminal's own report:** OSC 11, or the mode 2031 query in section 3.
3. **`COLORFGBG`:** set by rxvt, Konsole and a few others, e.g. `15;0`. The last field is the background index; 0–6 and 8 mean dark. SSH usually doesn't forward it, so it's a weak signal.
4. **Default to dark.**

Skip querying entirely if stdin or stdout isn't a TTY, or if `TERM=dumb`.

**Interpreting the reply:**
- Each channel can have 1–4 hex digits, so scale by the digit count.
- Compute luminance, e.g. `0.2126R + 0.7152G + 0.0722B`, and treat values below about 0.5 as dark.
- Accept both BEL and ST as the terminator.

**Multiplexers:** recent tmux answers OSC 11 itself with the pane's background color, which is what you want. GNU screen and older tmux may need passthrough wrapping or just won't answer, and the DA1 sentinel handles that gracefully.

## 3. Noticing OS theme changes

Don't read the OS setting yourself (e.g. `defaults read -g AppleInterfaceStyle`). Over SSH that reads the remote machine, and what matters anyway is the terminal's background, not the OS theme. Ask the terminal instead:

**Primary: mode 2031 (color-scheme change notifications).**
- Enable with `CSI ? 2031 h`.
- On every light/dark switch, a supporting terminal sends `CSI ? 997 ; 1 n` (dark) or `CSI ? 997 ; 2 n` (light).
- You can also ask for the current state with `CSI ? 996 n`.
- Support is growing: Contour (which proposed it), Ghostty, kitty, recent tmux and others. Check your target terminals, since my list may be behind.

**Fallback: re-check on focus-in.**
- Enable focus reporting with `CSI ? 1004 h`. You'll then get `CSI I` when the window gains focus.
- On each focus-in, send OSC 11 + DA1 again.
- People usually switch the OS theme from outside the terminal, so this catches nearly every real change at almost no cost, and many more terminals support it than 2031.

When the answer changes, swap the palette and do a full repaint. Ideally, look up colors by role ("accent", "muted") rather than storing hard-coded values, so swapping is one assignment.

**Cleanup:** turn off both modes (`CSI ? 2031 l`, `CSI ? 1004 l`) on exit, on suspend (SIGTSTP), and in your panic or crash handler. Turn them back on after resume (SIGCONT). Otherwise the user's shell gets escape-sequence junk after your app quits.

## Summary of the startup flow

```
resolve override / COLORFGBG / default → render first frame
if TTY && TERM != dumb:
    send OSC 11 + DA1; enable 2031 and 1004; send CSI ? 996 n
input loop:
    OSC 11 reply      → compute luminance → set theme
    DA1 before OSC 11 → note "no OSC 11 support", keep current theme
    997;1n / 997;2n   → set dark / light
    focus-in          → re-send OSC 11 + DA1
    (a user override always wins; ignore detected changes when one is set)
```

If you share the code that does the detection now, I can point out where it blocks and sketch the change in your language and TUI library. Some libraries, such as Bubble Tea/termenv and crossterm-based stacks, already have pieces of this.
