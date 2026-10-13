The fix is to stop waiting for the terminal before the first frame. Draw a default palette right away, ask about the background in the background, and switch palettes whenever an answer arrives, whether that's at startup or later. All three problems you describe come from treating the reply as something startup depends on, when it should only ever upgrade the colors.

## 1. Work out the theme in priority order

1. **Explicit user choice.** `--theme dark|light`, a config key or an env var. If this is set, skip detection entirely, because the user knows best and it removes all query cost. Default to `auto`.
2. **Instant hints.** If `$COLORFGBG` is set (rxvt-style terminals), use it as the starting guess.
3. **Built-in default.** Pick a palette that stays readable on both light and dark backgrounds. Avoid near-white or near-black text and subtle grays, which disappear on one of the two. Use semantic tokens (`accent`, `muted`, `error`…) so switching palettes means rebuilding styles, not editing call sites.
4. **The terminal's answer (OSC 11).** When it arrives, swap the palette and redraw.

## 2. Ask without stalling

- **Send two queries in the same write:** `OSC 11 ; ? ST`, followed immediately by DA1 (`CSI c`). Every terminal answers DA1. If the DA1 reply arrives first, no background reply is coming, so stop waiting at once. This handles terminals that never answer OSC 11: the Linux console, PuTTY, mosh, GNU Screen and ConEmu.
- **Cap the wait anyway.** Neovim uses 100 ms locally and lazygit allows 500 ms for slow SSH. Over SSH every query is a network round trip, so allow more time when `$SSH_TTY` or `$SSH_CONNECTION` is set. Either way the UI is already on screen.
- **Read replies through the app's normal input parser.** Don't run a separate blocking `read()` on stdin. A side reader competes with the framework for input, can swallow the user's first keystrokes and blocks the event loop. This is the likely cause of your SSH stall.
- **Parse `rgb:rrrr/gggg/bbbb`** (components can be 1–4 hex digits). Compute relative luminance and treat anything below about 0.5 as dark.
- tmux 3.4 and later answer OSC 11 themselves with the attached client's colors, so detection works inside tmux.

## 3. Follow OS theme changes (mode 2031)

- **Check support first:** send DECRQM `CSI ? 2031 $ p`. If it's supported, enable it with `CSI ? 2031 h`.
- **Change reports:** the terminal then sends `CSI ? 997 ; 1 n` when it switches to dark and `CSI ? 997 ; 2 n` when it switches to light.
- **On a report, send OSC 11 again** rather than trusting the report alone (lazygit and Neovim do the same). Then rebuild styles and force a full redraw.
- **Supported by:** kitty 0.38.1+, Ghostty, foot 1.23+ and iTerm2 3.7+. tmux 3.8 forwards the outer terminal's theme changes. WezTerm does not support it.
- **Turn it off in two places:** on every exit path (`CSI ? 2031 l`), and before handing the terminal to a child process such as `$EDITOR`. Turn it back on when you resume. The framework won't undo modes you enabled yourself.
- **Fallbacks for other terminals (my suggestion):** a manual toggle key, plus sending OSC 11 again when focus returns if you already enable focus reports (mode 1004). Under tmux, focus reports need `focus-events on`.

## 4. Framework notes

- **Bubble Tea v2:** return `tea.RequestBackgroundColor` from `Init` and handle `tea.BackgroundColorMsg` with `lipgloss.LightDark(msg.IsDark())`. Don't call `lipgloss.HasDarkBackground` inside a running program, because its query competes with Bubble Tea for input. Bubble Tea delivers 2031 reports to you but doesn't enable the mode, so enabling it is your job.
- **Textual, Ink, Ratatui/crossterm:** none of them handle 2031, so you'd do the probe and parsing yourself. If you tell me which framework you use, I can give you the exact wiring.

## 5. Tests

- **Unit tests:** the OSC 11 reply parser (different digit widths, both `BEL` and `ST` terminators), the priority order from section 1, and the luminance threshold.
- **Golden frames:** snapshot both palettes, plus `NO_COLOR`/monochrome. Meaning must survive without color either way.
- **One PTY test with a fake terminal that answers DA1 but never OSC 11.** Assert that the first frame appears immediately and that keystrokes typed during the query window aren't lost. This test would have caught your SSH stall.
