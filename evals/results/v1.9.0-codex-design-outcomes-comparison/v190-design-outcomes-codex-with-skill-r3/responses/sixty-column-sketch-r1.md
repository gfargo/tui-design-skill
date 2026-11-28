Use **one full-width pane at 60×24**, with Commits shown initially. Repositories and commits alone require `28 + 40 = 68` columns, including borders, so they cannot fit side by side.

This is the exact 60-column, 24-row screen; the two header lines and footer are padded with spaces to column 60. Example repository and commits:

```text
1 Repos   [2 Commits]   3 Diff
repo: tui-design / main
+----------------------------------------------------------+
|> a1b2c3d Fix resize handling                              |
|  b2c3d4e Keep selection on refresh                        |
|  c3d4e5f Add commit search                                |
|  d4e5f6a Improve diff navigation                          |
|  e5f6a7b Handle empty repositories                        |
|  f6a7b8c Add repository picker                           |
|  a7b8c9d Update key help                                 |
|  b8c9d0e Initial import                                  |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
+----------------------------------------------------------+
Enter diff  Esc repos  Tab pane  ? help  q quit
```

The bordered pane occupies rows 3–23: **60 columns outside, 58 inside, 19 content rows**. Brackets identify the active pane; `>` identifies the selected commit without requiring color.

Users reach the other views as follows:

- **Enter:** selected repository → commits → selected commit’s diff.
- **Esc:** diff → commits → repositories. It first dismisses any open help or search.
- **1 / 2 / 3:** directly show Repositories, Commits, or Diff.
- **Tab / Shift+Tab:** cycle those same views, including hidden ones.
- **Up / Down and PgUp / PgDn:** navigate the active list or scroll the diff. Diff uses unified format; Left/Right scroll long lines.
- **?** opens contextual help; **q** quits outside text entry.

Each view retains its selection and scroll position when hidden. Resizing preserves the focused view rather than resetting users to Commits.

Use this explicit breakpoint policy. Since you supplied no diff minimum, I recommend **40 columns including borders**:

| Terminal width | Layout |
|---|---|
| 140 | `Repos 28 │ Commits 40 │ Diff 72` |
| 108–139 | Same three panes; diff receives the remainder |
| 80–107 | `Repos 28 │ Commits remainder`; Diff opens full-screen |
| 60–79 | One full-width pane, as sketched |
| 40–59 | Same single-pane navigation; shorten labels and truncate subjects with `...` |
| Below 40 columns or 8 rows | Too-small state |

The proposed **40×8 minimum** keeps the commit pane’s required width and allows two header rows, two border rows, three content rows, and one footer. Shorter usable windows show fewer records; they never squeeze in extra panes.

Below that minimum, replace the interface with `Need 40x8; resize or q to quit`, clipped to the available cells if necessary. Preserve all state and restore the layout immediately when space returns.

Chrome audit: one border layer, one selected-row marker, no per-row icons or repeated metadata. The border consumes 158 cells; headers and footer consume 180—about **23.5%** of the screen. Keep app logos, extra status bars, and nested boxes out of this layout.