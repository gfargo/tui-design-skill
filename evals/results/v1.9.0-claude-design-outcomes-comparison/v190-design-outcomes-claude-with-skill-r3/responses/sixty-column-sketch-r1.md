**At 60 columns only one pane fits.** The repo list and the commit list together need 28 + 40 = 68 columns, which is more than 60. So the screen shows one full-width pane. The panes become a stack you move through: Repos → Commits → Diff. Each pane keeps its own state.

## 60 × 24

The commit list is the pane you'd use most, so that's what's shown here. The top border shows where you are in the stack, and the bottom row lists the keys.

```
┌─ Repos › api-server › Commits ─────────────────── 3/412 ─┐
│ a3f9c21  Fix race in cache invalidation   mlopez      2h │
│ 7be0d44  Add retry budget to HTTP client  dchen       5h │
│>19c2e8f  Bump tokio to 1.41               renovate    9h │
│ e51a0b7  Refactor config loader into se…  ana         1d │
│ 0c4d9e2  Merge pull request #318 from d…  dchen       1d │
│ 88ad1f3  Document rate-limit headers      mlopez      2d │
│ 4f20b6c  Remove deprecated v1 endpoints   ana         3d │
│ b7719ea  Handle empty JSON body in POST   kwame       3d │
│ 2d6e0f5  Add metrics for queue depth      dchen       4d │
│ c90b3a8  Fix flaky test_shutdown_order    kwame       5d │
│ 61e4f7d  Pin rust-toolchain to 1.82       renovate    6d │
│ f3a8c05  Split worker pool by priority    mlopez      1w │
│ 0ab91d2  Initial OpenTelemetry tracing    ana         1w │
│ 5e7c3b9  Release v2.4.0                   dchen       2w │
│ 9d02a6e  Tighten CORS allowlist           kwame       2w │
│ a1c7f40  Cache compiled templates         ana         2w │
│ 3b85d1c  Fix off-by-one in pagination     mlopez      3w │
│ d4e6a97  Move migrations to sqlx          dchen       3w │
│ 7f13b2e  Add healthz and readyz probes    kwame       4w │
│ e2c95a4  Log request IDs on every error   ana        1mo │
│ 6a0f8b3  Upgrade axum to 0.7              renovate   1mo │
└──────────────────────────────────────────────────────────┘
 Enter diff  Esc repos  / filter  ? help  q quit
```

How the space is used:
- **Rows:** 1 for the top border with the title, 21 commits, 1 for the bottom border, 1 for the key hints.
- **Columns:** 2 for borders and 2 for padding, leaving 56 for content:
  - hash: 7
  - gap: 2
  - subject: 31, cut off at the end with `…` when too long
  - gap: 2
  - author: 8
  - gap: 2
  - age: 4, right-aligned
- **Selected row:** reverse video plus a `>` in the padding cell. Only the selected row gets a marker. That's one visual cue and one text cue, so the selection still shows without color.
- **Clutter:** one border between the terminal edge and the content, no outer frame, and no column-header row.
- **Long titles:** if a repo name doesn't fit in the top border, shorten the middle of the breadcrumb and keep the `3/412` counter.

## How the user reaches what's off screen

| From | Key | Goes to |
|---|---|---|
| Repos | `Enter` | Commits for that repo |
| Commits | `Enter` | Diff for the selected commit: a full-width unified diff, with `]`/`[` to jump between hunks and `←`/`→` to scroll long lines |
| Commits | `Esc` | Repos, with the cursor still on the repo you came from |
| Diff | `Esc` | Commits, with the cursor still on the same commit |
| Anywhere | `1` `2` `3` | Jump straight to Repos, Commits or Diff. Use the same keys in the wide layout so habits carry over. |
| Diff | `J` / `K` | Next or previous commit without leaving the diff. Without these, browsing history at this width means pressing `Esc`, `j`, `Enter` for every commit. |

Some rules that keep this predictable:
- **Resizing keeps focus.** If you shrink from 140 to 60 columns, the pane that had focus becomes the visible pane. When you widen again, the other panes come back and the cursors haven't moved.
- **Launching at 60 columns** opens the Commits pane for the last repo used. If there isn't one yet, it opens Repos.
- **The breadcrumb and `Esc` hint stay visible**, so it's always clear that other panes exist.

The full width ladder:

| Width | Layout |
|---|---|
| 108 or more | All three panes: 28 + 40 + a diff of at least 40. At 140 the diff gets 72. |
| 80–107 | Commits and diff side by side (40 + 40 or more). The repo list becomes an overlay you open with `1`. |
| 40–79 | One pane, as sketched above |

## Smaller than 60

- **59 down to 45 columns:** still one pane. The subject column absorbs the lost space.
- **Below 45 columns:** the subject would drop under 16 characters, so hide the author column. The full author is still one `Enter` away in the diff header. Shorten the key hints to `? help  q quit`.
- **At 40 columns:** the floor. You get hash, subject (21) and age. The repo pane (28) fits easily. The diff gets 36 columns of content and scrolls sideways.
- **Narrower than 40 columns or shorter than 10 rows:** don't draw a broken layout. Show this instead, wrapped to fit whatever space there is:

```
Terminal too small (36x8).
Need at least 40x10.
Resize, or press q to quit.
```

While that message is up, `q` and `Ctrl+C` still quit. Everything else (which pane you're on, the selection, scroll positions) is kept, so making the window bigger again puts you back where you were. Tell users the real minimum, 40×10, not 80×24, because this layout really does work at 40.

To make sure it holds, take snapshot tests at 140×24, 80×24, 60×24, 40×10 and 39×10. Then resize a session from 140 down to 60 and back, and check that focus and selection survive.
