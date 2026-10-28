No existing code here to match, so this is a fresh design. I assumed these eight actions: **open, find, copy, move, rename, new, delete, quit**, plus `?` for help.

## 80 columns

```
 ↵ open  / find │ c copy  m move  r rename  n new  d delete │ ? help  q quit
```
That's 76 columns, leaving a 4-column margin. Writing to the last column of an 80-column terminal can cause a wrap or scroll on some terminals, so the line stops short of it.

## 40 columns

```
 ↵ open  / find  c copy  m move  ? more
```
That's 39 columns.

## Why it's built this way

- **The format is always `key label`.** Keys are bold in the accent colour and labels are dim. Two spaces separate items and one space joins a key to its label, so pairs still read correctly with no colour at all.
- **Actions are grouped: navigate │ edit │ app.** The dim `│` dividers make an eight-item line quick to scan. The dividers are dropped below about 60 columns, which saves 6 columns.
- **Labels never get abbreviated.** You won't see `del` at one width and `delete` at another. An item is either shown in full or hidden.
- **Items are hidden in a fixed priority order** when the line doesn't fit. The first to go is `new`, then `rename`, `delete`, `quit`, `move`, `copy`, `find`, and last `open`. Delete goes early on purpose: a narrow footer shouldn't use its few slots on the destructive key.
- **When anything is hidden, `? help` changes to `? more`.** This tells the user the footer is incomplete and how to see everything. The `?` item is never dropped.

## Other widths, to check the rule

```
60:  ↵ open  / find │ c copy  m move  d delete │ ? more  q quit
30:  ↵ open  / find  c copy  ? more
```

## Implementation sketch

Keep the actions as a list ordered by priority. Add items in that order, measuring display width with something like `wcwidth`, not string length, until the next one won't fit. Then render the chosen items in their display order. If the terminal can't draw `↵`, use `enter` instead and measure again.
