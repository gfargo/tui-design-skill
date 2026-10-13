# Treat the background query as an optional upgrade, not a startup step

Show the first frame right away using a default palette. Ask the terminal in the background, and switch palettes if an answer arrives. All three of your symptoms come from treating the background reply as something startup must wait for. The design below fixes each one.

## 1. Settle what you can without asking

Pick the palette in this order, and stop at the first rule that applies:

1. **The user's explicit choice.** Support `--theme dark|light|auto` and a config key, with `auto` as the default. If the user chose dark or light, send no query.
2. **`NO_COLOR` or no TTY.** Output is monochrome, so there's nothing to detect.
3. **`$COLORFGBG`.** rxvt-style terminals set it. It's a cheap first guess, but still send the query to confirm it.
4. **The OSC 11 query.** See section 2.
5. **The built-in default.** This is the palette for the first frame, and the final answer if nothing replies.

## 2. Query without stalling (fixes SSH and the silent terminals)

- **Add a reply every terminal sends.** In a single write, send OSC 11 (`ESC ] 11 ; ? ESC \`) and then DA1 (`ESC [ c`). Terminals answer in order, so if the DA1 reply arrives first, no background reply is coming and you can stop waiting immediately. The Linux console, PuTTY, mosh, GNU Screen and ConEmu never answer OSC 11. With this check, you find that out in one round trip instead of waiting for a timeout.
- **Still cap the wait.** Neovim waits 100 ms, lazygit 500 ms (to allow for slow SSH) and Lip Gloss 2 s. The cap only controls when you stop listening. It must never delay the first frame.
- **Keep SSH costs low.** Each query costs a network round trip, so send all your startup queries in one write and never one after another. A slow answer just causes a palette swap a little later.
- **Use one input reader.** Parse replies out of the app's normal input stream. Don't read the TTY separately at the same time. A second reader competes for bytes, and a late reply can leak into the app as fake keystrokes.
- **Parse the reply carefully.** It looks like `rgb:rrrr/gggg/bbbb`, and each part can have 1–4 hex digits. Scale each part to 0–1, compute luminance, and treat anything below about 0.5 as dark.
- **tmux 3.4+** answers OSC 11 itself with the attached client's colors, so the same code works inside tmux.

## 3. Follow OS theme changes (mode 2031)

- **Check for support** with DECRQM (`CSI ? 2031 $ p`), then enable the mode with `CSI ? 2031 h`.
- **On a theme-change report** (`CSI ? 997 ; 1 n` for dark, `CSI ? 997 ; 2 n` for light), send OSC 11 again rather than trusting the report alone, as lazygit and Neovim do. Then rebuild the styles and force a full redraw.
- **Supported by:** kitty 0.38.1+, Ghostty, foot 1.23+, iTerm2 3.7+, and tmux 3.8, which passes on the outer terminal's change. WezTerm doesn't support it.
- **Turn 2031 off** (`CSI ? 2031 l`) on every exit path, and before handing the terminal to `$EDITOR` or a shell. After resuming, turn it back on and query OSC 11 again, because the theme may have changed while you were away.
- **For terminals without 2031,** I'd also send OSC 11 again whenever the window regains focus (mode 1004). It's cheap and catches a theme switch the next time the user comes back. tmux only passes focus events on with `focus-events on`.

## 4. Make swapping palettes cheap

This only works if colors come from semantic tokens (`accent`, `muted`, `error`, …) with a light and a dark value each, rather than color literals scattered through the code. Then switching is one change to the theme followed by a redraw. If the swap is visibly jarring, that usually points to hard-coded colors that need to become tokens.

## Framework notes

- **Bubble Tea v2:** return `tea.RequestBackgroundColor` from `Init`, then handle `tea.BackgroundColorMsg` with `lipgloss.LightDark(msg.IsDark())` and rebuild the styles. Don't call `lipgloss.HasDarkBackground` inside a running program, because it competes with Bubble Tea for input; that matches your stall symptom. Bubble Tea passes 2031 reports through but doesn't enable the mode, so you need to send `CSI ? 2031 h` yourself.
- **Textual, Ink, Ratatui:** none of them handle 2031, so you parse the reports yourself. With crossterm/Ratatui, also undo the mode on exit yourself, since `restore()` only undoes raw mode and the alternate screen.

If you tell me which framework you're using, I can sketch the exact code.

## Tests

- **Unit tests:** reply parsing (1–4 hex digits per part, BEL vs ST terminators, junk input), the precedence rules, and the "DA1 arrived first, so stop waiting" logic.
- **Frame snapshots:** render frames with both palettes, plus `NO_COLOR`.
- **One PTY test:** start against a terminal that never answers and check that the first frame appears without waiting for the timeout.
