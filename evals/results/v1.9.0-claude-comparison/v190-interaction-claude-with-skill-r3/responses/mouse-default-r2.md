**Short answer:** Turn on modes **1000 + 1002 + 1006** in the full-screen TUI. Add **1003** only if you actually draw hover effects. Leave the mouse **off** in the inline picker.

## Full-screen TUI

| Mode | What it gives you | Enable? |
|---|---|---|
| `1000` | Button press and release | Yes |
| `1002` | Drag events (while a button is held) | Yes, if you have scrollbars, drag-select, or drag-to-reorder |
| `1006` | SGR encoding | Yes, always together with 1000/1002 |
| `1003` | Every pointer move, even with no button down | Only for hover styling |

- **Why 1006 is required:** without it, clicks past column 223 can't be encoded, and release events don't say which button was let go. Wide terminals and ultrawide splits hit the column limit.
- **Why to skip 1003 by default:** it sends an event every time the pointer crosses a cell. That means more traffic and more redraws (and slower SSH sessions) for nothing, unless something on screen reacts to hover.
- **Use the smallest set you need.** Watch your framework's defaults:
  - crossterm's `EnableMouseCapture` turns on *all* the modes, including 1003.
  - Textual turns on all-motion by default.
  - Bubble Tea and Ratatui leave the mouse off until you enable it.
- **Turn off whatever you turn on, on every exit path:** normal quit, error, panic, and suspend or editor handoff. Send `CSI ? 1006 l`, `1002 l`, and `1000 l`. Ratatui's `restore()` only undoes raw mode and the alternate screen. If capture is left on, the user's shell fills up with escape-sequence garbage every time they click.

**Rules for using it:**
- The mouse speeds things up but never gates anything. Every click target needs a keyboard equivalent. Good uses: focusing a pane, switching tabs, scrolling lists and viewports, clicking buttons. The wheel scrolls the viewport under the pointer, not the selection.
- **Provide an off switch,** such as `--no-mouse` or a config key. Any mouse mode takes over the terminal's native click-and-drag text selection.
- **Document how to bypass it for selection.** The modifier depends on the terminal: Shift in most terminals, Option in iTerm2, Fn in Terminal.app.

## Inline picker: leave it off

An inline picker sits inside the user's scrollback and shell context, which is the reason for making it inline in the first place. If you enable mouse reporting:
- Users can no longer select and copy nearby output without knowing the bypass modifier.
- Wheel scrolling of the terminal's own scrollback stops working while the picker is open.
- One crash or Ctrl+C path that skips cleanup leaves capture on in the user's shell.

The gain doesn't cover that. A bounded picker is fast with arrows, typing to filter, and Enter. fzf is the exception: it enables the mouse but never requires it. If you follow that model, make it opt-in and keep every action on the keyboard.

**tmux note:** since tmux 3.8 the `mouse` option defaults to on. If your inline picker doesn't enable reporting, a plain drag inside tmux starts tmux's copy-mode selection and the wheel enters copy mode. That's acceptable, because it's what users get in their shell anyway. But your docs shouldn't promise native terminal selection inside tmux. Ctrl-drag and Alt-drag always go to tmux, so don't build anything on them.
