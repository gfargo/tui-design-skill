Treat theme detection as **optional, asynchronous terminal input**. A terminal that never replies must still start normally.

1. **Offer `auto`, `light`, and `dark`.** An explicit choice wins over detection and subsequent notifications. In `auto`, render immediately with a documented fallback palette; use terminal-default foreground/background where practical.

2. **Query without blocking startup.** Send the OSC 11 background query (`ESC ] 11 ; ? ST`) after your terminal input parser is running. Handle the reply through the same event loop as keyboard input—avoid a separate reader that could consume keystrokes. Give detection a short deadline, perhaps 200–500 ms, but don’t delay the first frame. No reply means “unknown,” not an error.

3. **Parse replies defensively.** OSC replies can arrive fragmented or mixed with keyboard input. Support BEL and ST terminators and variable-width RGB components; normalize those components before calculating luminance. Bound message length and tolerate malformed replies. Keep recognizing valid late replies after the deadline so they don’t appear as typed text.

4. **Subscribe to theme changes where supported.** Supporting terminals expose color-scheme notifications through private mode **2031**. You can probe support with DECRQM, enable notifications with `CSI ? 2031 h`, and request the current scheme with `CSI ? 996 n`. Reports are `CSI ? 997 ; 1 n` for dark and `CSI ? 997 ; 2 n` for light. Handle these as events, update the palette, and redraw. Restore any terminal mode you changed on exit.

5. **Provide a fallback for older terminals.** OSC 11 reports the current background; it does not guarantee future notifications. Without notification support, re-query on focus gain or an explicit “refresh theme” action, with throttling and the same nonblocking behavior. Avoid continual polling.

The relevant theme is **the local terminal’s theme**. Over SSH, the remote machine’s OS appearance tells you nothing about the terminal displaying the TUI. Even locally, an OS theme change matters only if the terminal follows it and exposes the change. SSH, tmux, and screen can also delay or filter queries, so capabilities must remain optional.

Test no reply, delayed and fragmented replies, typing during detection, malformed responses, theme changes, and explicit overrides. The central guarantee should be: **startup never waits for theme detection, and detection never steals user input.**