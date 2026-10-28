**Short answer:** make confirmation dialogs 60–80% of the terminal width, with a minimum of 30 columns and a maximum of about 80. Center them horizontally and place them slightly above vertical center. Under `NO_COLOR`, the border, the title, the cleared background and the changed footer hints tell the user they're in a dialog. Dimming the screen behind it only helps where it works; nothing should depend on it.

## Width

A rule that works:

```
width = clamp(round(cols * 0.7), 30, 80)
width = min(width, cols - 2)        # always leave a 1-cell margin each side
left  = (cols - width) / 2
top   = max(0, (rows - height) / 2 - 1)   # nudge up from true center
```

- **At most ~80 columns:** wider than that and lines of text get too long to read comfortably.
- **At least 30 columns:** below that, the question and buttons wrap badly.
- **Recompute on every resize** from the current size. Don't store the dialog's size from when it opened.
- **Below about 32 columns** (my suggestion, not a fixed rule): use the full width without margins, or show your app's "terminal too small" state. Don't draw a dialog that overflows the screen.

**80×24 (width 56):**
```
┌ Files ───────────────────────────────────────────────────────────────────────┐
│ src/                                                                         │
│ ┌ Delete files ──────────────────────────────────────────┐                   │
│ │                                                        │                   │
│ │  Delete 3 files? This cannot be undone.                │                   │
│ │                                                        │                   │
│ │    main.go                                             │                   │
│ │    util.go                                             │                   │
│ │    util_test.go                                        │                   │
│ │                                                        │                   │
│ │                       [ Delete ]  [> Cancel <]         │                   │
│ └────────────────────────────────────────────────────────┘                   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
 DIALOG  y delete · n/Esc cancel · Tab switch
```

**60-column tmux split (width 42):**
```
┌ Files ───────────────────────────────────────────────────┐
│      ┌ Delete files ──────────────────────────┐          │
│      │                                        │          │
│      │  Delete 3 files? This cannot be        │          │
│      │  undone.                               │          │
│      │    main.go                             │          │
│      │    util.go  … +1 more                  │          │
│      │                                        │          │
│      │           [ Delete ]  [> Cancel <]     │          │
│      └────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────┘
 DIALOG  y delete · Esc cancel
```

At 60 columns the text wraps and the file list is cut short with "… +1 more". The buttons and the key hints stay. Measure text in terminal cells, not string length, so CJK characters and emoji don't break the border.

## Showing a modal under `NO_COLOR`

`NO_COLOR` turns off color. It doesn't turn off text attributes, so bold, reverse video and underline are still available. Make the dialog recognizable without color in these ways:

1. **Clear the cells behind it.** Fill its rectangle with blanks before drawing, so text underneath doesn't show through. Monochrome makes bleed-through much more confusing.
2. **Give it its own border and a title.** `┌ Delete files ─┐` marks it as a separate layer even with no styling.
3. **Change the footer hints.** Replace the app's usual hints with the dialog's keys, and optionally add a `DIALOG` label. This is the most reliable sign that the input mode has changed.
4. **Show the focused button with reverse video plus brackets**, like `[> Cancel <]`. Reverse video works on every terminal, and the brackets still work if reverse is ignored.
5. **Dim the background only as an extra.** The faint attribute isn't a color, so you can use it under `NO_COLOR`, but some terminals ignore it.
6. **Show the default in the text.** For the light-friction case, use `[y/N]` or make Cancel the default focus, so pressing Enter doesn't delete anything.

## Behavior rules

- **One modal at a time.** A new request replaces the current dialog or waits behind it.
- **The modal traps focus**, and each `Esc` press closes one modal.
- **Match the friction to the consequence:**
  - A y/n prompt for routine actions.
  - Typing the resource's name for destructive actions like "delete prod-main".
  - Typing plus a second y/n only for rare, catastrophic actions.
  - Don't require typing everywhere, or people learn to type through it without thinking.
- **Test with snapshots** of the dialog at 80×24, at 60 columns and at your minimum size, both with and without `NO_COLOR`. Check that the border, title, footer and focus marker are still clear in the monochrome frames.

If you tell me your framework (Bubble Tea, Ratatui, Textual, Ink), I can show the specific overlay and clear-background code for it. They handle this quite differently: Ratatui has a `Clear` widget, Textual has `ModalScreen`, and Bubble Tea needs manual compositing.
