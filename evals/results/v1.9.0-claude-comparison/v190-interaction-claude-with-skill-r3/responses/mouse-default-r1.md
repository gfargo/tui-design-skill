**Full-screen TUI:** turn on modes 1000, 1002 and 1006. Don't turn on 1003 unless you actually draw hover effects. Give users a way to switch mouse capture off. **Inline picker:** leave the mouse off.

## Full-screen TUI

| Mode | What it adds | Enable? |
|---|---|---|
| `CSI ? 1000 h` | Button press and release | Yes |
| `CSI ? 1002 h` | Drags while a button is held | Yes, for drag-select, resizing panes, scrollbars |
| `CSI ? 1006 h` | SGR coordinate encoding | Always, alongside the others |
| `CSI ? 1003 h` | Every pointer move, even with no button pressed | Only if you render hover states |

- **Why 1006:** without it, coordinates break past column 223 and you can't tell which button was released. Every terminal supports it, so there's no reason to leave it out.
- **Why not 1003 by default:** it sends an event on every pointer movement, which means extra events to process and extra redraws for nothing visible.
- **Check your framework's defaults.** crossterm's `EnableMouseCapture` turns on every mode, 1003 included. If you want the smaller set, write the sequences yourself; in Rust you then also own disabling them. Textual turns on all-motion tracking by default. Bubble Tea v2 and crossterm/Ratatui start with the mouse off.
- **Restore on every exit path.** Send the matching `l` sequences on normal exit, errors, panics and suspend, and re-enable them when you resume. A crash that leaves mouse capture on fills the user's shell with escape-sequence garbage.

**Treat the mouse as an extra.** Use it for focusing panels, switching tabs, scrolling (the wheel scrolls the viewport under the pointer, not the selection) and clicking buttons. Every action you can reach by mouse also needs a key.

**The cost: capture takes over native text selection.** Users have to hold a bypass modifier to select text: Shift in most terminals, Option in iTerm2, Fn in Terminal.app. Document this, and add a `--no-mouse` flag or a config key. helix and fzf both work this way: mouse on by default, never required, easy to disable.

## Inline picker: leave it off

An inline picker draws into the user's normal scrollback. If you capture the mouse there, you break the two things that make inline worth having:
- Click-and-drag selection of text above the picker stops working.
- Wheel scrolling through scrollback stops working.

A picker's main path is type to filter, arrows to move, Enter to pick and Esc to cancel. A mouse adds little to that.

**tmux 3.8+ caveat:** the `mouse` option now defaults to on. In an app that hasn't enabled mouse reporting, a plain drag starts tmux's copy-mode selection. The wheel also enters copy mode, except on the alternate screen. Your picker doesn't need to do anything about this, but users may need to know, so it's worth a line in your docs.

**Exception:** if the picker ever switches to the alternate screen, for example for a large preview pane like fzf's full-screen mode, the full-screen rules above apply.
