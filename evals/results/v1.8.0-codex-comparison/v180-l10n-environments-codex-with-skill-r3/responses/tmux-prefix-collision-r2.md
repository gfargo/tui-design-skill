**Give the sidebar a non-prefix shortcut, and keep Esc with a fast alternative such as Ctrl+G for leaving insert mode.** Both symptoms come from input handling before your app receives a key.

- **Ctrl+B is tmux’s default prefix.** tmux consumes it and waits for a tmux command; your TUI never receives that first press. With the default bindings, **Ctrl+B, Ctrl+B** sends a literal Ctrl+B to the app. That’s a workaround, not a good primary interaction.
- **Esc is ambiguous in legacy terminal encoding.** A standalone Esc is the same initial byte used by Alt combinations and many special-key sequences. tmux waits for more bytes before deciding which it is. Its `escape-time` default was **500 ms before tmux 3.5**, and is **10 ms since 3.5**; user configuration can override it. Your input library may add another timeout.

Design around this by:

1. **Providing a portable sidebar path.** For a modal app, use something like `Space b` in normal mode, plus a “Toggle sidebar” command. Make bindings configurable; replacing Ctrl+B with Ctrl+A just collides with GNU Screen and common tmux configurations.
2. **Keeping Esc conventional.** Add Ctrl+G as an equivalent insert-mode exit, document both, and show a persistent `INSERT`/`NORMAL` label. Printable sidebar shortcuts must yield to text entry.
3. **Supporting modern keyboard protocols when negotiated.** Kitty keyboard disambiguation can encode Esc distinctly, but support must survive the terminal–multiplexer–app chain. Retain legacy bindings.
4. **Offering optional tmux tuning.** Users can put this in `~/.tmux.conf`:
   ```tmux
   set -s escape-time 10
   ```
   Lower values reduce delay but can misparse sequences on slow connections. Don’t silently modify their configuration.

Verify outside tmux, inside tmux, and over SSH: standalone Esc, Alt combinations, arrows, and quick typing immediately after leaving insert mode. Measure key arrival separately from mode transition to locate any remaining delay.

For the sidebar itself, preserve the main pane at 80×24 and use an overlay or single-pane view in a 60-column split. Keep shortcut hints contextual and compact; without a screenshot, there’s no evidence to count border or marker clutter.