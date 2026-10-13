**Keep Enter to send, but make Ctrl+J the always-available newline binding. Treat Shift+Enter as an optional accelerator.** Show `Enter send · Ctrl+J newline` beside the composer; advertise Shift+Enter only when the input path supports it.

The problem is terminal encoding. In legacy input, Enter and Shift+Enter commonly produce the same byte: carriage return (`0x0D`). Once that happens, Bubble Tea cannot recover the Shift modifier. Kitty’s keyboard protocol preserves it, which explains why kitty works. Inside tmux, support depends on its version, configuration, and the outer terminal; extended keys are commonly disabled.

Bubble Tea v2 negotiates enhanced keyboard input, but negotiation cannot guarantee that every layer preserves modifiers. `$TERM` or “running in kitty” alone is insufficient evidence.

The design should be:

| Input | Composer action |
|---|---|
| Enter | Send a nonempty draft |
| Ctrl+J | Insert newline—legacy encoding uses LF (`0x0A`) |
| Distinct Shift+Enter event | Insert newline |
| Bracketed paste | Insert the entire text, including newlines; never send |

In implementation, handle `tea.KeyPressMsg` and match the complete key binding (`"shift+enter"`, `"ctrl+j"`, `"enter"`). Checking only the Enter key code can accidentally classify a modified Enter as send even when its modifier survived. Consume send events before forwarding input to the textarea, and configure its newline bindings explicitly.

Offer a persistent **“Enter inserts newline”** preference for people composing longer messages, with a separate send binding such as Ctrl+S and a keyboard-accessible Send control. Avoid silently changing Enter’s meaning as capability replies arrive.

For tmux troubleshooting, document `set -s extended-keys on` as a possible prerequisite, alongside version and outer-terminal support. It is an enhancement, not a requirement for composing multiline messages.

Verify both model behavior and real input: kitty directly, kitty inside tmux, and a legacy terminal. Log decoded key code/modifiers to a file; if both presses arrive identically, the information was lost upstream.

Keep the UI small: one composer boundary and one hint line, without repeated shortcut badges. At 80×24 and in a 60-column split, preserve the composer and its hints, hide any sidebar, and let message history give up space as the composer grows.