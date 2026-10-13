The working directory is empty, so I can't see how your TUI does this now. Here's how I'd design it based on the three symptoms you describe.

## Why it's breaking

1. **SSH stalls:** The app most likely sends `OSC 11` (`\e]11;?\e\\`) and then blocks reading stdin until a reply arrives or a timeout fires. Over SSH a round trip can take hundreds of milliseconds, so any timeout is either too short (you miss the answer) or too long (startup visibly hangs).
2. **Terminals that never answer:** Many terminals don't support `OSC 11` and just ignore it. Your only clue is silence, so you wait out the whole timeout. If the reply comes late, it can also show up as garbage keystrokes like `]11;rgb:…`.
3. **No theme updates:** You ask once at startup and never again.

## Recommended design

### 1. Use DA1 as a marker instead of guessing a timeout
Send the background query and then a Primary Device Attributes request in one write:

```
\e]11;?\e\\   \e[c
```

Almost every terminal answers DA1 (`\e[?…c`), and terminals reply in order. So:
- If the `OSC 11` reply comes before the DA1 reply, use it.
- If the DA1 reply comes first, the terminal doesn't support the query. You know immediately, with no timeout and no matter the latency.

Keep a long safety timeout (around 1–2 s) only for very broken setups. It should almost never fire.

### 2. Don't block startup on the answer
- Draw the first frame with your best guess (see the order below), then redraw if the answer differs. A brief color flip looks much better than a frozen screen.
- Read the replies in your normal input loop, not in a separate blocking read before the loop. The input parser should recognize `OSC 11`, DA1 and the mode-2031 reports from the next step, and drop them, so they never reach the app as keys. This also fixes the garbage-text problem and keeps keys the user types during startup.
- Switch to raw mode (no echo) before sending any query. Otherwise the reply gets printed to the screen.
- Only send queries when both stdin and stdout are TTYs.

### 3. Decide light or dark in this order
1. An explicit user setting (a config option or `--theme=light|dark`). Always give users a way to override detection.
2. An app-specific environment variable, such as `YOURAPP_THEME`.
3. The terminal's answer to `OSC 11`.
4. `COLORFGBG`, if set (e.g. `15;0` means a light foreground on a dark background). It's useful as the first-frame guess.
5. Default to dark.

To parse the `OSC 11` reply, accept both the `BEL` and `ST` terminators. Each `rgb:R/G/B` component can have 1–4 hex digits, so scale each one by its own width. Compute relative luminance and treat anything above about 0.5 as light.

### 4. Live theme changes
- **Preferred: DEC mode 2031** (color-scheme updates). Enable it with `\e[?2031h`. The terminal then sends `\e[?997;1n` when it switches to dark and `\e[?997;2n` when it switches to light. You can also ask for the current state with `\e[?996n`. Ghostty, kitty, Contour and some others support it, and support keeps growing.
- **Fallback: re-check on focus.** Enable focus reporting (`\e[?1004h`) and send `OSC 11` + DA1 again on every focus-in (`\e[I`). People usually change their OS theme while they're in another window, so this catches most changes even on terminals without 2031. The check costs almost nothing.
- Turn off 2031 and 1004 on exit and on suspend (`SIGTSTP`), and turn them back on when resumed (`SIGCONT`). Otherwise the shell receives stray reports.

### 5. tmux and screen
Inside tmux, `OSC 11` is answered by tmux, not by the outer terminal. Recent tmux versions report a sensible color, and newer releases also handle theme-change reporting. Older versions or unusual setups may give you something wrong or stale, which is one more reason the user override has to exist. Don't try to wrap queries in DCS passthrough by default. It needs `allow-passthrough` to be on, and it breaks in confusing ways.

## Summary
Send `OSC 11` + DA1 together without blocking, handle the replies in the normal input parser, and draw a guessed theme first and correct it after. Listen for mode 2031 and re-check on focus-in. Let explicit user settings override all of it.

If you point me to the code (or tell me the language or framework, e.g. Bubble Tea, Ratatui, Textual), I can sketch the actual changes.
