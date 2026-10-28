**Use unified at 100 columns and side-by-side at 160.** Pick the mode from the current width on every resize, and switch at 120 columns. At 120 or more, each side gets at least 55 columns plus a 2-cell gutter. Below that, two panes would each be too narrow to read real code. Also give users one key, say `s`, to override the automatic choice for the rest of the session.

## 160 columns: side-by-side

Shown here at about half scale.

```
 src/auth/session.ts   3/12 files   hunk 2/5          ±  +14 −6
 files          │  41  if (!token) {            │  41  if (!token) {
 ▸ session.ts   │  42- return null;             │  42+ throw new AuthError(
   login.ts     │                               │  43+   "missing token");
   token.ts     │  43  }                        │  44  }
                │  44- const ttl = 3600;        │  45+ const ttl = cfg.ttl;
 ]/[ hunk  s unified  f files  ←/→ scroll  ? help
```

- **Width budget:** a file list of 24–30 columns, then two diff sides of about 64 columns each. Each side spends 5 columns on line numbers and 2 on the `+`/`-` sign and a space, which leaves about 57 for code. If the file list would push the code area below 55 columns, the file list folds away first. That happens before the layout drops to unified.
- **Align rows:** a deleted line faces its added replacement. Lines that exist on only one side get a blank filler row opposite them, so the two sides never drift apart.
- **No wrapping:** cut long lines with `…` and scroll both sides together with `←`/`→`.
- **Borders:** use one thin divider between the sides. Don't put a separate box around each side.

## 100 columns: unified

```
 src/auth/session.ts                       3/12 files  hunk 2/5  +14 −6
   41   41    if (!token) {
   42       -   return null;
        42  +   throw new AuthError("missing token");
        43  +     "missing token");
   43   44    }
 ]/[ hunk  f files  s split  ←/→ scroll  ? help
```

- **Gutter:** two line-number columns (old and new), then the sign. That costs about 12 columns and leaves about 88 for code.
- **File list:** hide it by default at this width, because the standard band (80–119 columns) gives the primary view the full width. The header shows `3/12 files`, and `f` opens the file list as an overlay. A permanent sidebar here would squeeze the code down to about 60 columns.
- **Forced side-by-side:** if the user presses `s` at 100 columns, each side gets about 42 code columns. Allow it, but truncate lines instead of wrapping them.

## Rules for both modes

- **Signs as well as color:** every changed line starts with `+` or `-`, and color only reinforces it. Word-level highlights inside a changed line need a non-color fallback under `NO_COLOR`, such as reverse video or underline.
- **Same navigation:** `]` and `[` jump between hunks in both modes, and the keys don't change when the mode does.
- **Keep the place on resize:** when the layout switches between unified and side-by-side, keep the same hunk and line at the top of the screen. A user dragging the window past 120 columns should never lose their position.
- **Width measurement:** truncate by terminal cell width, not string length. Otherwise CJK text or emoji in the code will shift the gutters out of line.

## Smaller sizes

- **80×24:** unified with no file list. You get about 18 visible diff lines after the header and footer.
- **60-column tmux split:**
  ```
   session.ts  3/12  h2/5   +14 −6
   42    -   return null;
     42  +   throw new AuthErr…
   ]/[ hunk  f files  ? help
  ```
  Show only the new line numbers on unchanged lines. Truncate the path from the start so the filename survives. Shorten the footer.
- **Below about 50×10:** show a "terminal too small, need 50×10" message instead of a broken layout.

## Clutter audit

- **Borders:** at most one level of nesting (the divider). Don't box the diff panes.
- **Signals per changed line:** two, the sign and the color. Don't add row background color, a third signal, on top of those.
- **Repeated text:** the file path appears once in the header, not on every hunk.

## Tests

Snapshot rendered frames at pinned sizes: 160, 120 and 119 (both sides of the switch), 100, 80×24, and 60 columns. Run each with and without `NO_COLOR`.

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual or Ink), I can map this onto its layout constraints and resize events.
