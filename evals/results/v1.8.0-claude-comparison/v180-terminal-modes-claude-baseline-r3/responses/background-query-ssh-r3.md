The working directory is empty, so I can't see your implementation. All three symptoms usually come from the same design: a blocking query at startup, followed by a timeout. Here's the approach I'd recommend.

## 1. Stop guessing with timeouts: send a DA1 query after the background query

Send both queries in a single write:

```
ESC ] 11 ; ? ESC \     # OSC 11: what's your background color?
ESC [ c                # DA1: primary device attributes
```

Almost every terminal answers DA1, and terminals answer in order. So:
- If the OSC 11 reply arrives first, you have the color.
- If the DA1 reply arrives with no OSC 11 reply before it, the terminal doesn't support OSC 11. You know right away, with no waiting.

This removes the "some terminals never answer" stall. Keep a generous safety timeout (about 1–2s) only for badly broken setups. It should almost never fire.

## 2. Never block startup on the answer

The SSH stall happens because you're waiting a full network round-trip before drawing anything. Instead:

1. Choose an initial theme right away, using the fallback chain below.
2. Draw.
3. Send the queries, and handle the replies in your **normal input parser** as ordinary events.
4. When a reply arrives and differs from your guess, switch theme and redraw.

Parsing replies in the main input loop, not in a separate blocking read, also fixes two bugs that often go with this: user keystrokes typed during startup getting swallowed, and late replies showing up as garbage like `]11;rgb:...` in the input. Your parser should accept both the `ESC \` and `BEL` terminators.

## 3. Get live theme changes from the terminal, not the OS

Don't read the OS setting (`AppleInterfaceStyle`, etc.). Over SSH you'd be reading the wrong machine, and the user's terminal theme may not follow the OS anyway. Use these instead:

- **Mode 2031 (color-scheme change notifications):** enable with `ESC [ ? 2031 h`. Supporting terminals then send `ESC [ ? 997 ; 1 n` (dark) or `ESC [ ? 997 ; 2 n` (light) whenever their scheme changes. You can also ask for the current value with `ESC [ ? 996 n`. Supported by Contour, Ghostty, kitty and a growing list of others. When a notification arrives, re-send OSC 11 if you want the exact color.
- **Fallback: re-query on focus-in.** Enable focus events with `ESC [ ? 1004 h`. On `ESC [ I`, send OSC 11 again. It's cheap, and it covers terminals without 2031: the user usually switches the theme in another app and then comes back.

On exit (including on signals and panics), disable both with `ESC [ ? 2031 l` and `ESC [ ? 1004 l`.

## 4. Order of precedence

1. **Explicit user setting**: a config option, flag or env var such as `MYAPP_THEME=light|dark|auto`. This is always the escape hatch for setups that get detection wrong.
2. **Live terminal report**: OSC 11 or a 2031 notification.
3. **`COLORFGBG`**: set by rxvt, Konsole and some others. A last field of `0`–`6` or `8` means dark. Use it only as the initial guess.
4. **Default to dark.**

## 5. Details that trip people up

- **Parsing:** each channel in `rgb:R/G/B` can be 1–4 hex digits. Scale each by its own maximum (`0xF`, `0xFF`, `0xFFF`, `0xFFFF`), not by assuming 16-bit. Then compute relative luminance (`0.2126R + 0.7152G + 0.0722B`, linearized if you want to be precise) and treat < 0.5 as dark.
- **When to skip querying:** don't query if stdin or stdout isn't a TTY, or if `TERM=dumb`.
- **Multiplexers:** recent tmux versions answer OSC 11 themselves. Older tmux and GNU screen may swallow the query, but the DA1 reply still arrives, so you fall back cleanly. That's another reason DA1 beats a timeout. Avoid DCS passthrough wrapping unless you really need it.
- **Re-query rate:** re-query at most once per event. Don't poll on a timer.

In short: draw immediately using your best guess, and send OSC 11 plus DA1 without blocking. Treat the replies and the 2031/focus-in events as ordinary input that can change the theme at any time, and always let the user override detection.

If you can point me at the code, I can make these changes in your terminal library.
