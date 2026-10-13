Make theme detection **asynchronous, bounded, and optional**. Draw the first frame immediately, then adapt when terminal replies arrive. Follow the terminal’s appearance: over SSH, the remote OS theme says nothing about the user’s terminal.

1. **Offer `--theme auto|light|dark`.** Default to `auto`; explicit choices win over detection. Use semantic color tokens, a readable fallback with terminal-default foreground/background, and honor `NO_COLOR`.

2. **Bound the background query.** Send `OSC 11 ; ? ST`, followed by DA1 (`CSI c`) or a status query (`CSI 5 n`) as a sentinel. If the sentinel replies before OSC 11, finish detection with the fallback. Also enforce a deadline—**500 ms is a reasonable starting point for SSH**—because either reply can be missing. This deadline must never delay rendering or keyboard input. Terminals such as PuTTY, the Linux console, mosh, and GNU Screen may never answer OSC 11.

3. **Handle replies through the existing input parser.** Terminal responses share the keyboard stream; avoid a second reader that can steal keystrokes. Parse RGB component widths correctly, accept fragmented sequences, and safely consume late replies. A valid background reply can update the automatic palette and trigger a redraw.

4. **Subscribe to appearance changes where supported.** Probe mode 2031 with DECRQM (`CSI ? 2031 $ p`), using another bounded request. When supported:
   - Enable notifications: `CSI ? 2031 h`.
   - Request current appearance: `CSI ? 996 n`.
   - Recognize `CSI ? 997 ; 1 n` as dark and `CSI ? 997 ; 2 n` as light.
   - On a notification, **re-query OSC 11** to confirm the actual background before choosing the palette. Coalesce repeated notifications.

5. **Keep unsupported terminals usable.** Mode 2031 support varies; an OS theme switch is observable only if the terminal follows it and exposes the change. Provide a runtime theme selector or refresh command. Optionally re-query on focus return or resume, with the same timeout. Disable notifications before handing control to a child process or exiting; re-establish them after resuming.

Keep detection invisible: no startup dialog, spinner, or persistent warning. Switching palettes should preserve focus, selection, and layout.

Verify missing replies, delayed SSH replies, interleaved typing, fragmented responses, runtime changes, explicit overrides, and terminal handoff. The key acceptance criterion is: **a terminal that never answers must still start promptly and remain fully usable.**