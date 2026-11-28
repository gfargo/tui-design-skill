At **60×24, show one full-width pane**, defaulting to commits. Repositories plus commits already need **28 + 40 = 68 columns**, before giving the diff any space.

This sketch is exactly **60 columns × 24 rows**, including borders. Example repository and commits:

```text
+ 1 Repos | [2 Commits] | 3 Diff --------------------------+
| demo / main                                              |
+----------------------------------------------------------+
|> a1b2c3d Fix resize handling                             |
|  b2c3d4e Keep selection when switching panes             |
|  c3d4e5f Add unified diff view                           |
|  d4e5f6a Load repositories                               |
|  e5f6a7b Initial commit                                  |
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
|                                                          |
+----------------------------------------------------------+
| Commit 1/5 | Enter diff | Esc repos                      |
| 1/2/3 pane  Tab next  Up/Down move  ? help  q quit       |
+----------------------------------------------------------+
```

The commit pane has **58 interior columns** and **17 data rows**. `[2 Commits]` marks the active pane; `>` marks the selected commit.

Everything remains reachable:

- **1 / 2 / 3** switches directly to repositories, commits, or diff. **Tab / Shift+Tab** cycles through them.
- **Enter** on a repository opens its commits; Enter on a commit opens its diff. **Esc** returns one level, after dismissing any open help or search.
- Each pane remembers its selection and scroll position. Switching panes replaces the content without adding another border.
- **Up/Down, PgUp/PgDn** reveal additional rows. Diff uses unified format; **Left/Right** scroll long lines horizontally. Commit subjects truncate with `...`; the commit detail exposes the full message.
- On resize, retain the focused pane. If the user was reading the diff, keep the diff visible instead of jumping to commits.

Use this width ladder; **40 columns is a proposed minimum for the diff**:

```text
140 columns:  Repositories 28 | Commits 40 | Diff 72
 80 columns:  Commits 40      | Diff 40    (repositories via 1)
 60 columns:  Active pane 60               (1/2/3 switch)
```

All widths include borders; there are no extra gutters. Three panes fit at **108+ columns**, two at **80–107**, and one below 80.

For smaller terminals, declare a supported minimum of **40×8**: the commit pane still meets its 40-column requirement, with at least one data row. Shorten context and hints as space shrinks, retaining `1/2/3`, `?`, and quit access. Below either minimum, replace the layout with:

```text
Terminal too small
Need 40x8; have 39x7
Resize or q to quit
```

Clip that message to the available cells in extremely small terminals. Preserve all state and restore the layout immediately when space returns.

Clutter check: one border layer, one active-tab cue, one selection marker. This frame spends 434 of 1,440 cells—about **30%**—on chrome; avoid adding nested pane boxes, repeated repository labels, or markers on every row.