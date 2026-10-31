## 80 columns

```
⏎ open  / filter  j/k move  r refresh  d delete  y copy  e edit  ? help  q quit
```

This line is 79 columns. I left the last column empty because writing to it makes some terminals wrap or scroll. Each hint is separated by two spaces, so the hints don't run together.

Three hints don't fit: `s sort` (4%), `t tag` (3%) and `: command` (2%). They're the least-used actions, and `? help` lists them.

## 40 columns

```
/ filter  r refresh  ? help  q quit
```

This line is 35 columns. No other hint fits in the 4 left over, since the shortest one needs 8 including its separator.

**What I dropped at 40 and why:**

- **`⏎ open` (90%)**: I dropped this even though it's the most-used action. A key hint is there to help people find things, and pressing Enter to open a file is something everyone already tries. The 90% figure shows people found it without a hint, so the space is better spent on something they wouldn't guess.
- **`j/k move` (35%)**: I'm assuming the arrow keys also move the cursor, which is what most people will try. The hint mainly tells vim users what they would already guess. **If arrows don't work in your app, put `j/k move` back in place of `r refresh`** (34 columns).
- **`d delete`, `y copy`, `e edit`**: These are used 8% of the time or less and don't fit.
- **`s sort`, `t tag`, `: command`**: These were already dropped at 80.

**Why `/ filter` stays:** at 40% it's the second most-used action, and nobody would guess the `/` key without being told.

**Why `? help` and `q quit` stay at every width:** your logs show no usage for them, but they matter most. `?` leads to every hint that was dropped, and `q` is the way out. Without them the dropped hints can't be found and users can't easily leave.

## Implementation rule

Give each hint a priority and drop hints from the lowest priority up until the line fits. Never drop the pinned ones:

1. Pinned: `? help`, `q quit`
2. `/ filter`, `r refresh`, `j/k move`, `⏎ open`, `d delete`, `y copy`, `e edit`, `s sort`, `t tag`, `: command`

This list puts `⏎ open` and `j/k move` below their usage rank. That's on purpose, for the reasons above. Since they'll be dropped earlier, they still show at 80 columns, where new users get the most from the full set.

**Note:** `⏎` (U+23CE) is one column wide in standard terminals. If your users' fonts might not have that symbol, use `enter` instead. It's 4 columns longer, so at 80 columns you'd also need to drop `e edit`.
