Make theme detection **asynchronous, bounded, and optional**. Draw immediately with a usable fallback; terminal replies should update the palette without delaying startup.

1. **Provide `--theme auto|light|dark`.** Default to `auto`; explicit choices override detection and subsequent notifications. Use semantic color tokens, terminal-default foreground/background where practical, and honor `NO_COLOR`.

2. **Bound the initial background query.** Send `OSC 11 ; ? ST`, followed by DA1 (`CSI c`) or a status query (`CSI 5 n`) as a sentinel. A sentinel reply without an earlier background reply lets you stop waiting. Keep a hard timeout anyway—**500 ms is a reasonable starting budget for SSH**, while the UI remains interactive throughout. Unsupported terminals and intermediaries may never answer either query.

3. **Parse replies through the existing input event loop.** Don’t add a competing stdin reader or discard keyboard input while probing. Accept valid background replies, including late ones while in auto mode; classify their brightness, update semantic tokens, and redraw. On timeout or malformed data, retain the fallback silently.

4. **Subscribe to live appearance changes where supported.** Probe mode 2031 with DECRQM (`CSI ? 2031 $ p`). If supported, enable it with `CSI ? 2031 h`; `CSI ? 996 n` requests the current theme. Notifications arrive as:
   - `CSI ? 997 ; 1 n` — dark
   - `CSI ? 997 ; 2 n` — light

   Treat a notification as a trigger to **re-query OSC 11**, using the same bounded process, then repaint. Coalesce bursts rather than issuing overlapping probes.

5. **Handle unsupported notifications and terminal handoffs.** Offer a runtime theme selector; optionally re-query on focus return or resume. Disable mode 2031 before yielding to a child process and during cleanup, then re-enable and refresh on return.

Follow the **terminal’s appearance**, which may differ from the OS theme. Over SSH, the terminal protocol reaches the user’s local emulator; checking the remote machine’s OS theme won’t solve this. Live updates depend on emulator and multiplexer support—tmux 3.4+ answers OSC 11, while theme forwarding requires tmux 3.8.

Verify delayed replies, no replies, sentinel-only replies, malformed responses, typing during detection, live switches, explicit overrides, and suspend/child-process cleanup. The essential acceptance criterion: **theme detection never stalls startup or consumes user keystrokes.**