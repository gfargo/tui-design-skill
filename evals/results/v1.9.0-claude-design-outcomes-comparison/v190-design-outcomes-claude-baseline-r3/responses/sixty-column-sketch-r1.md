At 60 columns the three panes can't fit side by side. Repos (28) plus Commits (40) is already 68, before the diff gets any room. So the screen shows **one pane at a time, full width**, with a tab strip on top that names the panes you can't see. The Commits pane is the default because it's the main view.

## 60 × 24

```
  1 Repos   [2 Commits]   3 Diff                 api-server 
┌─ Commits · main ───────────────────────────────── 2/248 ─┐
│   a41c9e0  Add retry backoff to webhook   priya      2h  │
│ ▶ 7d02b4f  Fix race in pool shutdown      maria      5h  │
│   e5f81aa  Bump golang.org/x/net to v0.3… renovate   1d  │
│   3b9c7d2  Refactor config loader         alex       1d  │
│   c0ffee1  Document rate limit headers    sam        2d  │
│   8a7e6f5  Remove deprecated v1 routes    priya      3d  │
│   19dd0b3  Add healthcheck endpoint       maria      4d  │
│   f4e2a90  Tighten CORS defaults          alex       6d  │
│   2c8b1e7  Cache repo metadata in memory  sam        1w  │
│   b7a3d58  Fix flaky TestServeHTTP        priya      1w  │
│   6e1f0c4  Split handlers into packages   maria      2w  │
│   d93a2b6  Add structured logging         alex       2w  │
│   0a5c7e9  Upgrade to Go 1.23             renovate   3w  │
│   5f8d1b2  Handle SIGTERM gracefully      sam        3w  │
│   a2e9c31  Fix nil deref in auth middle… priya     1mo  │
│   7c4b0d8  Add pagination to /commits     maria     1mo  │
│   e8f3a17  Rename Store to Repository     alex      2mo  │
│   4d6b2c0  Add Makefile                   sam       2mo  │
│   91be5f3  Initial CI workflow            priya     3mo  │
│   ab0c3e2  Initial commit                 maria     3mo  │
└──────────────────────────────────────────────────────────┘
 ←/→ panes  1-3 jump  ↑↓ move  enter diff  ? help  q quit
```

How the rows add up: 1 tab strip + 22 for the pane (20 commits plus the 2 border rows) + 1 key-hint footer = 24. Every line is exactly 60 columns, borders included.

- **Tab strip (row 1):** always shows every pane. The brackets mark the visible one (draw it in reverse video in the real UI). The current repo name sits on the right, so you still know where you are while the Repos pane is hidden.
- **Title bar:** `2/248` tells you the list scrolls and where you are in it.
- **Long subjects** get cut off with `…` so the author and age columns stay aligned.

## How the user gets to what's hidden

| Action | Result |
|---|---|
| `enter` on a commit | Opens **Diff** full width for that commit (the tab strip becomes `1 Repos   2 Commits   [3 Diff]`) |
| `esc` or `←` in Diff | Back to Commits, with the same commit still selected |
| `←` in Commits, or `1` | Opens **Repos** full width |
| `enter` on a repo | Loads it and jumps to Commits |
| `←`/`→` | Moves one pane left or right |
| `1` / `2` / `3` | Jumps straight to a pane |

Each pane keeps its selection and scroll position when you leave it. Going back and forth between list and diff should feel like drilling in and out, not starting over.

If the terminal is widened again, the layout switches back by itself, keeping whichever pane was focused:
- **80 to 107 columns:** Commits and Diff side by side, with Repos still reached through its tab.
- **108 or more:** all three panes (28 + 40 + at least 40 for the diff).

## Smaller than 60 × 24

**Narrower (59 down to 40 columns):** same single-pane layout. The Commits pane gives up columns in this order:
1. The subject gets shorter.
2. At about 50 columns, the author column goes.
3. At 40 columns (38 inside the borders) it's down to marker, hash, a short subject and age. That's the 40-column minimum you set.

**Shorter (fewer than 24 rows):** the list shows fewer commits, and the position counter keeps it obvious that you're scrolling. Below about 12 rows the footer is dropped, but `?` still opens help. Below about 8 rows nothing useful is left.

**Below 40 columns or 8 rows:** don't squeeze the panes any further. Clear the screen and show only a centered message, cut down so it fits even in a tiny window:

```
Terminal too small
 39×24 — need 40×8
  resize, or q to quit
```

While the message is showing, the app keeps all its state, still responds to `q`, and redraws the normal layout as soon as the terminal is resized back over the minimum.
