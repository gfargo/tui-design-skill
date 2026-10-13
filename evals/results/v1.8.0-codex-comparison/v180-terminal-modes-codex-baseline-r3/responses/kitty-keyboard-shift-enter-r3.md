This is a terminal protocol limitation, not necessarily a Bubble Tea bug.

In traditional terminal input, **Enter and Shift+Enter often produce the same byte**, usually carriage return (`\r`). Once that reaches your app, there is no Shift information to recover. Kitty’s enhanced keyboard protocol can encode modifiers explicitly. Inside tmux, that information must survive both the terminal→tmux and tmux→app hops; versions and configuration matter.

Bubble Tea v2 can handle distinct key events **when the terminal stack actually delivers them**. A `"shift+enter"` binding cannot distinguish two identical incoming events.

The design should be:

- **Enter sends; Shift+Enter inserts a newline when distinguishable.** Request enhanced keyboard reporting through Bubble Tea’s supported mechanism.
- **Always provide a portable newline shortcut**, such as Ctrl+O, and show it in the composer’s help. Make bindings configurable. Ctrl+Enter has the same portability problem; Ctrl+J can collide with Enter in some setups.
- **Route composer shortcuts before the textarea’s default handling.** Consume send/newline events so they do not also trigger another action. If enhanced reporting includes release events, act on presses; consider suppressing repeat for send.
- **Preserve pasted multiline text without sending it.** Handle bracketed paste as text, rather than interpreting pasted newlines as send commands.
- **Adapt help to observed capabilities**, not `$TERM`, a kitty executable, or the presence of tmux. Advertised protocol support also does not guarantee that a particular shortcut reaches the app unchanged.

For diagnosis, inspect the decoded key code and modifiers in kitty directly, in the affected terminal, and through tmux. If both gestures arrive as unmodified Enter, the distinction was lost upstream.

If preventing accidental sends is a hard requirement, offer a mode where **Enter inserts a newline and an explicit shortcut sends**. You cannot universally guarantee both “Enter sends” and “Shift+Enter never sends” on terminal stacks that encode them identically.