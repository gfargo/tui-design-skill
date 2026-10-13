Both problems come from tmux interpreting input before your TUI receives it.

**Ctrl+B is tmux’s default prefix key.** tmux consumes it and treats the next key as a tmux command, so your app never sees the first Ctrl+B. With the default bindings, pressing **Ctrl+B twice** sends one literal Ctrl+B to the application—but that’s a workaround, not a good primary interaction.

**Esc is ambiguous in terminal input.** The Escape byte can mean “the user pressed Esc,” or it can begin an arrow/function-key sequence or an Alt-key combination. tmux waits briefly to distinguish these cases, controlled by `escape-time`. Your TUI’s input parser may also wait, so the delays can stack.

Design around this by:

- **Making shortcuts configurable**, and avoiding Ctrl+B as the sole sidebar shortcut. Provide an alternative default, such as F2, plus a discoverable command or menu action. Check your defaults against tmux, terminal, and shell bindings.
- **Keeping Esc, but offering another way to leave insert mode.** Ctrl+G is a reasonable option; Ctrl+[ typically produces the same Escape byte and therefore usually has the same delay.
- **Checking your input library’s Escape timeout.** Keep it short and configurable, while testing arrow keys, function keys, Alt combinations, and slower SSH connections.
- **Supporting negotiated keyboard protocols where available**, with a legacy fallback. They can disambiguate keys, but require support throughout the terminal → tmux → application path.

For affected users, document this optional tmux setting:

```tmux
set -sg escape-time 10
```

That gives tmux a 10 ms ambiguity window. Zero can feel faster but is less forgiving of fragmented input on slower connections. Treat this as user tuning; your app should have usable bindings without requiring users to change tmux.