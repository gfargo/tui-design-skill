The directory is empty, so this design isn't tied to any framework. I picked eight common file-manager actions; swap in your own and the rules still apply.

## Design

**Order:** Actions go left to right by how likely someone is to need the hint. Navigation comes first, then actions that change files, then actions people already know.

| Priority | Key | Label | Why it's here |
|---|---|---|---|
| 1 | `⏎` | open | most-used action |
| 2 | `⌫` | up | moving around is basic |
| 3 | `c` | copy | changes files |
| 4 | `m` | move | changes files |
| 5 | `d` | delete | changes files, but it asks to confirm anyway |
| 6 | `r` | rename | used less often |
| 7 | `/` | find | many users already know it |
| 8 | `q` | quit | almost everyone knows it |
| always shown | `?` | help / more | way out to the full list |

**Styling:** Each key is bold in the accent color and each label is dim. A hint is the key, one space, then the label (`c copy`). Hints are separated by two spaces, with no pipes or brackets; the color change already marks where each hint starts.

**The `?` slot** sits flush right and never drops off. It reads `? help` when every hint fits and changes to `? more` once any are hidden, so the user can tell something was cut.

**Narrowing rule:** Drop whole hints from the lowest priority up until the bar fits. Never shorten labels (`cp`, `mv`, `ren`); half-words are harder to read than missing hints.

## 80 columns: everything fits

```
 ⏎ open  ⌫ up  c copy  m move  d delete  r rename  / find  q quit        ? help 
```

The eight hints take 65 columns, then an 8-column gap, then `? help` and a 1-column margin on each side, for exactly 80.

## 40 columns: priority cut

```
 ⏎ open  ⌫ up  c copy  m move    ? more 
```

The top four hints take 28 columns, then a 4-column gap, `? more` and the margins, for exactly 40. Delete, rename, find and quit still work; they just aren't shown. `d delete` (10 columns with its gap) is the next to come back, at about 50 columns.

Pressing `?` at any width opens the full list, which also fits in 40 columns:

```
┌─ keys ───────────────────────────────┐
│ ⏎  open           r  rename          │
│ ⌫  up             d  delete          │
│ c  copy           /  find            │
│ m  move           q  quit            │
└────────────────────────── esc close ─┘
```

## Implementation notes

- **Glyph fallback:** `⏎` and `⌫` are 1 column wide in most terminals but may not exist in some fonts. Spelling them out (`enter`, `bksp`) adds 7 columns, which costs one hint at 40 columns. Pick one at startup rather than mixing.
- **Measure, don't guess:** Measure each hint's display width (with something like `wcwidth`), not its string length, and lay the bar out again whenever the terminal is resized.
- **Context swap:** When files are selected, consider replacing the bar with a selection-mode set (`c copy 3  m move 3  d delete 3  esc clear`) instead of adding hints to it. Fewer hints are easier to scan, and the same cutting rules apply.
