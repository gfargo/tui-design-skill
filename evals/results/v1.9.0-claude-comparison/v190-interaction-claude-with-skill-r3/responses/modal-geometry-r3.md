**Short answer:** size the confirmation dialog to fit its content, between 30 columns at the low end and the smaller of 80% of the terminal or about 80 columns at the high end. Centre it horizontally, put it slightly above the vertical centre, and never let it touch the edges. Under `NO_COLOR`, show that it's a modal with structure rather than colour: blank the cells behind it, then add a border, a title, changed footer hints and a text-marked default.

## Width

The skill's rule for modals (`references/visual-patterns.md:483`, `:291`):

- **Upper limit:** 60–80% of the terminal width, and no more than about 80 columns for prose.
- **Lower limit:** 30 columns.
- **Confirmations are short, so fit them to the content.** Don't stretch a one-line question to 80% of a 200-column terminal.

```
w = clamp(text_width + 2*padding + 2*border, 30, min(80, floor(0.8 * cols)))
x = (cols - w) / 2
y = max(1, (rows - h) / 2 - 1)      # slightly above center
```

Measure `text_width` in terminal cells, not with `len()`, so file names with CJK characters or emoji don't break the box. If the terminal is narrower than about 34 columns, the dialog can't keep a margin. Either fill the width minus one column on each side, or show the "terminal too small" state.

**At 80×24:**
```
 ┌ files ───────────────────────────────────────────────────────────────────┐
 │ src/main.go                                                              │
 │ src/ui.go            ┌─ Delete files ───────────────────┐                │
 │ README.md            │                                  │                │
 │                      │  Delete 3 files? This cannot be  │                │
 │                      │  undone.                         │                │
 │                      │                                  │                │
 │                      │      [ No ]      Yes             │                │
 │                      └──────────────────────────────────┘                │
 └──────────────────────────────────────────────────────────────────────────┘
  DIALOG  y delete · n/Esc cancel · Tab switch
```

**In a 60-column tmux split:** the dialog is the same width because it was sized to its content, and there's still a margin on both sides:
```
 ┌ files ───────────────────────────────────────────────┐
 │ src/main.go                                          │
 │         ┌─ Delete files ───────────────────┐         │
 │         │                                  │         │
 │         │  Delete 3 files? This cannot be  │         │
 │         │  undone.                         │         │
 │         │                                  │         │
 │         │      [ No ]      Yes             │         │
 │         └──────────────────────────────────┘         │
 └──────────────────────────────────────────────────────┘
  DIALOG  y delete · n/Esc cancel
```

## Showing a modal under `NO_COLOR`

Dimming the background isn't enough on its own. Faint is a text attribute, not a colour, and some terminals ignore it (`visual-patterns.md:486`). Each of these cues works with no colour at all:

1. **Blank the cells behind the dialog** so the list underneath doesn't show through.
2. **Give it its own border and a title** that names the action ("Delete files", not "Confirm").
3. **Change the footer.** Replace the normal hint bar with only the dialog's keys, and optionally add a `DIALOG` label. That tells users the keymap has changed.
4. **Mark the focused button with text.** Use `[ No ]` brackets or `>`, not only a highlight colour. Reverse video and bold are attributes rather than colours, so they're fine as an extra cue.
5. **Trap focus.** Only the dialog's keys work, and `Esc` closes this dialog only (`interaction-patterns.md:190`, `:98`).
6. **Dim the background with faint where the terminal supports it,** but only as a bonus.

## The confirmation itself

Match the friction to the cost (`interaction-patterns.md:305`):

- **Easily reversible actions:** `[y/N]` with **No** as the default, so pressing Enter by reflex doesn't delete anything.
- **Things like "delete production":** make the user type the name.
- **Rare, catastrophic actions:** type a word, then a y/N prompt.

Don't require a typed name for everything. People learn to type it without thinking, and it stops protecting them.

**Tests to add:** snapshot (golden) tests of the dialog at 80×24, at 60 columns and at your minimum size, each run once with colour and once with `NO_COLOR=1`. The `NO_COLOR` snapshot should still make it obvious which screen is a dialog and which button is focused.

If you tell me your framework (Bubble Tea, Ratatui, Textual or Ink), I can show the overlay and clear-behind code for it.
