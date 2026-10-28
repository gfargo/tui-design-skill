**Width:** use the content width, kept between 30 columns and the smaller of 80% of the terminal or about 80 columns. Center it horizontally and place it a little above the vertical middle.

**NO_COLOR:** the border, the title and the changed footer hints must show that a dialog is open. Dimming and color can help, but nothing should depend on them.

## Sizing

The skill's guidance is: dialogs take 60–80% of the terminal width, at most about 80 columns for prose, at least 30. Below that range, size to the content, and never run edge to edge. A confirmation is short, so in practice it sizes to its content:

```
inner  = max(cell_width(longest line), cell_width(button row)) + 2*padding   // padding = 1–2 cells
width  = clamp(inner + 2 /*border*/, 30, min(80, floor(0.8 * term_cols)))
x      = (term_cols - width) / 2
y      = max(0, (term_rows - height) / 2 - 1)   // slightly above center
```

- Measure terminal **cell width**, not string length, so file names with CJK characters or emoji don't break the border.
- Truncate long items with `…`, or summarize them ("3 files"), instead of making the dialog wider.
- **Floor:** in a 60-column tmux split, 80% is 48 columns, which still fits. If the terminal is too narrow for a 30-column box plus margins, my suggestion is to drop the box and show a one-line prompt in the status bar: `Delete 3 files? [y/N]`.

**80×24:**
```
 Files  Commits  Branches
  src/old.go
  src/tmp.go         ┌─ Delete files ─────────────────────────┐
  README.bak         │                                        │
                     │  Delete 3 files? This can't be undone. │
                     │                                        │
                     │  src/old.go, src/tmp.go, README.bak    │
                     │                                        │
                     │         [ No ]     Yes                 │
                     └────────────────────────────────────────┘

 DIALOG  y yes · n/Esc no · Tab switch · Enter choose
```

**60 columns** (the file list truncates instead of widening the box):
```
      ┌─ Delete files ─────────────────────────┐
      │                                        │
      │  Delete 3 files? This can't be undone. │
      │                                        │
      │  src/old.go, src/tmp.go, README.b…     │
      │                                        │
      │         [ No ]     Yes                 │
      └────────────────────────────────────────┘
 DIALOG  y yes · n/Esc no · Enter choose
```

## Making it read as a dialog under NO_COLOR

1. **Clear the cells behind the box** so the screen underneath doesn't show through. Without background color, this is what separates the dialog from the screen.
2. **Give it its own border and a title** that names the action ("Delete files"), not just "Confirm".
3. **Change the footer.** Swap the normal key hints for the dialog's keys and add a label such as `DIALOG` or `CONFIRM`. Users who missed the box still see that the keymap changed.
4. **Dimming is optional.** You can fade the background with the faint attribute, but faint is a text attribute, not a color, and some terminals ignore it. Steps 1–3 must work on their own.
5. **Mark the focused button without color:** brackets (`[ No ]`), plus reverse video or bold. Those are text attributes, and NO_COLOR only turns off color.
6. **Use ASCII borders as a fallback** (`+-|`) when you can't be sure the terminal supports box-drawing characters.

## Behavior

- **Default to No.** Pressing Enter right away should cancel, not delete.
- **Match friction to the risk:**
  - y/N for ordinary deletes.
  - Make the user type the resource name for something like "delete prod-main".
  - Ask twice only for rare, catastrophic actions. If everything requires typing, people learn to type fast and the check stops working.
- **One dialog at a time.** The dialog keeps keyboard focus. Esc closes only the top dialog and never quits the app.
- **Tests:** add snapshot tests of the dialog with `NO_COLOR=1` at 80×24 and 60 columns. Also check that the box still looks distinct when faint is off.

The rules come from `references/visual-patterns.md` (*Modals and dialogs*, *Honor NO_COLOR*) and `references/interaction-patterns.md` (*Confirmation patterns*). If you tell me your framework (Bubble Tea, Ratatui, Textual, Ink), I can show the overlay code for it.
