**Make theme detection optional, asynchronous, and bounded.** The TUI should be usable immediately, even if the terminal never replies. Follow the terminal’s appearance: an OS theme switch matters only when the terminal follows it.

Using the tui-design skill, I’d implement this contract:

1. **Offer `--theme auto|light|dark`, defaulting to `auto`.** Explicit choices override detection and subsequent notifications. In auto mode, render immediately with a readable fallback using terminal-default foreground/background and semantic ANSI colors. Honor `NO_COLOR`.

2. **Query the background without blocking startup.** Send `OSC 11 ; ? ST` through the interactive terminal and handle its reply through the existing input/event loop. Follow it with DA1 (`CSI c`) or a status query (`CSI 5 n`) as a sentinel: if that response arrives first, stop expecting an OSC 11 answer. Still enforce a deadline—**500 ms is a reasonable starting point for SSH**, while the UI remains responsive throughout.

   Some terminals and intermediaries never answer, including the Linux console, PuTTY, mosh, and GNU Screen. A timeout means “unknown,” not an error. Keep the fallback; accept a valid late reply while still in auto mode. Parse replies as protocol events so they cannot appear as keystrokes or enter text fields.

3. **Subscribe to changes where supported.** Probe mode 2031 with DECRQM:
   
   | Purpose | Sequence |
   |---|---|
   | Probe support | `CSI ? 2031 $ p` |
   | Enable notifications | `CSI ? 2031 h` |
   | Request current appearance | `CSI ? 996 n` |
   | Receive dark / light | `CSI ? 997 ; 1 n` / `CSI ? 997 ; 2 n` |
   | Disable notifications | `CSI ? 2031 l` |

   Bound the probe too. On a notification, re-query OSC 11 to confirm the actual background, then update semantic theme tokens and redraw. Coalesce repeated notifications.

4. **Provide a fallback for missing notifications.** Re-query on focus return or resume, with throttling and the same deadline, and offer a runtime theme selector. Focus reporting is itself optional. Without notification support, automatic changes cannot be guaranteed; `$COLORFGBG` is only a potentially stale initial hint.

5. **Own cleanup.** Disable any notification mode you enabled on exit, errors, suspend, and before handing the terminal to a child process. Re-establish detection on resume. Send no queries into redirected output or noninteractive input, and never introduce a second reader competing with the framework’s input parser.

Keep detection invisible: no startup spinner, timeout dialog, or permanent status marker. Theme updates should preserve focus and layout at both 80×24 and 60 columns.

Verify no reply, sentinel-only replies, delayed SSH replies, malformed or fragmented replies, theme changes, explicit overrides, and suspend/resume. The central invariant is: **terminal silence must never delay startup or swallow user input.**