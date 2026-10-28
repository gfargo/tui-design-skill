## Full-screen TUI (alternate screen)

**Enable:**

| Mode | Sequence | Why |
|---|---|---|
| 1000 | `CSI ?1000h` | Button press/release, including the wheel (buttons 64/65) |
| 1002 | `CSI ?1002h` | Motion while a button is held, which you need for drag (resizing panes, selecting a range) |
| 1006 | `CSI ?1006h` | SGR encoding: `CSI < b;x;y M/m`. It handles columns and rows past 223, tells you which button was released, and is easy to parse. Always use it. |

**Optional:**
- **1003** (any motion): only enable this if you actually render hover states. It sends a flood of events, so turn it on only while hover matters if you can.
- **1004** (focus in/out): not mouse reporting, but useful for pausing animations or redrawing on refocus.

**Avoid:** 1005 (UTF-8 encoding, which is ambiguous) and 1015 (urxvt encoding). 1006 replaces both. Don't use X10 mode 9 either.

**Handle these cases:**
- **Restore on every exit path.** Send `CSI ?1006l ?1002l ?1000l` on normal exit, on panic/crash, and on SIGTSTP (Ctrl-Z). Re-enable on SIGCONT. Otherwise the user's shell fills with garbage like `^[[<0;12;5M` every time they click.
- **Mouse capture breaks native text selection.** Most terminals let users bypass it with Shift-drag, or Option-drag in iTerm2 and Terminal.app. Mention this in your help, and provide a `--no-mouse` flag or config option.
- **Lighter option if you only want wheel scrolling:** leave mouse reporting off and rely on **1007 (alternate scroll)**. Many terminals turn it on by default in the alt screen, and it translates the wheel into Up/Down arrow keys. You get scrolling and native selection still works.

## Inline picker (no alt screen)

**Default: no mouse.** Keep it keyboard-driven.

- **It takes over the scroll wheel.** With reporting on, the user can't scroll back through their terminal history while the picker is open. In an inline UI, that history is the context they're looking at.
- **It breaks copy and paste** of nearby output.
- **Coordinates are screen-absolute.** You'd have to query your own position with DSR (`CSI 6n`) and track it whenever the picker sits at the bottom and the screen scrolls. That's fragile.
- **It's a short interaction.** Arrow keys, typing to filter, and Enter cover it. Users don't expect to click.

**If you do want clicking** (fzf enables it even in `--height` mode, for example), make it opt-in or easy to turn off. Enable only 1000 + 1006, never 1002 or 1003. Get your origin row with `CSI 6n` at startup. Disable reporting the moment the picker closes, including on Ctrl-C.

In short: use 1000 + 1002 + 1006 for full-screen, add 1003 only if you need hover, and always clean up. Keep the inline picker keyboard-only by default.
