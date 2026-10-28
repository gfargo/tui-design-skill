**Full-screen TUI:** enable 1000 + 1002 + 1006. Leave 1003 off unless you have hover effects. Add an off switch.
**Inline picker:** don't capture the mouse.

## Full-screen TUI

| Mode | Enable? | Why |
|---|---|---|
| `1000` (press/release) | Yes | Clicks to focus panes, switch tabs and press buttons |
| `1002` (button-event / drag) | Yes | Drag to select a range or resize a split. It only reports motion while a button is held, so traffic stays low. |
| `1006` (SGR encoding) | Yes, always with the others | Without it, coordinates past column 223 break and you can't tell which button was released |
| `1003` (any-event motion) | Only for hover effects | It reports every pointer move. If nothing in the UI reacts to hover, it's wasted input. |

Turn them on with `CSI ?1000h`, `CSI ?1002h` and `CSI ?1006h`. Turn them off (`…l`) on every exit path: normal quit, error, panic, and before handing the terminal to `$EDITOR` or a suspend. Leftover mouse capture is a classic way a TUI breaks the user's shell.

Enable the smallest set the UI needs. In Rust, crossterm's `EnableMouseCapture` turns on all of them, including 1003. If you don't want that, write the sequences yourself and you own the teardown. Bubble Tea and Ink have mouse reporting off by default. Textual turns on all motion.

**Rules that come with turning it on:**
- **The mouse speeds things up but is never required.** Every click target needs a key binding. Use the mouse for focusing panes, switching tabs, scrolling, and form buttons. Don't make it the only way to reach anything on the critical path.
- **The wheel scrolls the viewport under the pointer**, not the current selection.
- **Provide an off switch**, such as `--no-mouse` or a config key. Capturing the mouse takes over normal click-and-drag text selection.
- **Document the bypass modifier for selecting text.** It's Shift in most terminals, Option in iTerm2 and Fn in Terminal.app.
- **tmux 3.8+ has `mouse` on by default.** If your app enables reporting, it gets the events, but Ctrl-drag, Alt-drag and Alt+right-click still belong to tmux. Don't bind those.

## Inline picker

Inline tools leave the mouse off, and the reasons are specific to this kind of tool:
- **The user's scrollback and selection keep working.** A picker runs among the user's shell history. Capturing the mouse would block selecting or copying the text around it, which is often why they're there.
- **Clicking adds little.** The keyboard loop (type to filter, arrows or Ctrl+N/P, Enter) is faster for a choose-and-exit tool.
- **Restoring the terminal is safer.** A picker that gets killed mid-session and leaves mouse mode on garbles the next prompt with escape sequences. With nothing enabled, that can't happen.

If users ask for click-to-pick, make it opt-in (`--mouse`) rather than the default. fzf shows the trade-off: it does enable the mouse by default, at the cost of normal text selection while it's open. For a new picker, the safer default is off.

**Summary:** full-screen gets 1000 + 1002 + 1006 with keyboard equivalents, a `--no-mouse` switch and guaranteed teardown. The inline picker gets no mouse reporting.
