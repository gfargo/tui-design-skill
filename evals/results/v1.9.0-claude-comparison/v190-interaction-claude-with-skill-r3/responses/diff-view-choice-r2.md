**Pick the diff layout from the diff pane's own width, not the terminal's.** On a 160-column terminal, show the diff side by side. On a 100-column terminal, show a unified diff. Switch to side by side only when the pane can give each side at least 55 columns plus a 2-cell gutter between them, so the pane needs about 112 columns. Below that, use unified. Add a key (for example `s`) that lets the user override the automatic choice. If they force side by side and it doesn't fit, fall back to unified and say why in the status line. Don't squeeze the two sides.

A file list beside the diff takes some of that width. At 160 columns with a 30-column file list, the diff pane gets about 129 columns, which is enough for side by side. At 100 columns, the same file list leaves about 69 columns, which is only enough for unified.

## 160 columns: file list + side by side (drawn at half scale)

```
 Files (3)        │ src/parse.rs                                     
 M src/parse.rs   │ @@ -12,7 +12,8 @@ fn parse_header                 
 A src/lex.rs     │   12  let n = read(buf);  │  12  let n = read(buf);  
 D old/util.rs    │   13- if n == 0 {         │  13+ if n == 0 || eof {  
                  │                           │  14+     trace!("empty");
                  │   14      return None;    │  15      return None;    
 ───────────────────────────────────────────────────────────────────────
 ]/[ hunk  s unified  ←/→ scroll  Tab files  ? help              2/5 hunks
```

- When a line changes, show the old version on the left and the new one on the same row on the right. For a line that was only added or only removed, leave the opposite side blank so later rows still line up.
- Each side has its own line-number gutter. Mark a line's change with `+` or `-` next to the number. Color only reinforces that marker. Highlight only the words that changed inside the line (here, `|| eof`).
- Don't wrap long lines. Cut them off with `…` and scroll both sides left and right together with `←`/`→`.

## 100 columns: file list + unified

```
 Files (3)        │ src/parse.rs                         
 M src/parse.rs   │ @@ -12,7 +12,8 @@ fn parse_header     
 A src/lex.rs     │   12   12   let n = read(buf);       
 D old/util.rs    │   13      - if n == 0 {              
                  │        13 + if n == 0 || eof {       
                  │        14 +     trace!("empty");     
                  │   14   15       return None;         
 ─────────────────────────────────────────────────────────
 ]/[ hunk  s split  Tab files  ? help          2/5 hunks
```

Unified needs two line-number columns, old and new, which take about 10 cells. The code still gets about 55 columns. The file list keeps its place, so the layout doesn't move when the user resizes between the two widths.

## The floor: 80×24 and a 60-column tmux split

- **80×24:** the file list shrinks to about 24 columns (file paths are cut at the start so the file name stays visible), and the diff stays unified.
- **60 columns:** use a single pane. The file list fills the screen, `Enter` opens that file's diff at full width, and `Esc` goes back. Keep only the new line numbers to save about 5 cells.
- **Below about 40×10:** show "terminal too small, needs 40×10" until the user resizes. Don't draw a broken diff.

```
60 columns, after Enter on a file
 src/parse.rs                              2/5
 @@ -12,7 +12,8 @@ fn parse_header
   12   let n = read(buf);
      - if n == 0 {
   13 + if n == 0 || eof {
   14 +     trace!("empty");
   15       return None;
 ]/[ hunk  Esc files  ? help
```

## Clutter audit for the layouts above

- **Borders:** at most one level of nesting. A single `│` divider separates the panes. Don't put a box around the diff or around each hunk. The dim `@@` hunk header and a blank row are enough to separate hunks.
- **Change signals:** use exactly two, the `+`/`-` marker and color. Don't also add a background tint on the gutter, a row arrow, or an icon.
- **Markers on every row:** none. Context lines have no marker, so `+`/`-` stands out.
- **Space spent on chrome:** keep it low. The file name appears once, in the header, not on every hunk.

## Navigation and tests

- **Keys:** `]`/`[` (or `n`/`N`) jump between hunks in both layouts. Keep the same hunk in view when the layout changes on resize or when the user presses `s`.
- **Without color:** under `NO_COLOR`, the `+`/`-` markers and the hunk headers still carry the meaning. Changed words in a line need a non-color cue too, such as bold or underline.
- **Measuring width:** measure in terminal cells, not characters. CJK text and tabs break column alignment in the side-by-side view. Expand tabs before you measure.
- **Tests:** save expected screen output at 160, 100, 80×24 and 60 columns and at the minimum size. Include `NO_COLOR` versions, and a case that resizes across the 112-column threshold while the view stays on the same hunk.

The case where the layout switches is a pane between 112 and about 125 columns. Each side is then close to 55 columns, and many lines will be cut off. If your code uses long lines, raise the threshold to 120–130 columns rather than lowering the 55-column minimum per side.

If you tell me your framework (Ratatui, Bubble Tea, Textual, Ink), I can show how to compute the pane width and trigger the switch in its layout system.
