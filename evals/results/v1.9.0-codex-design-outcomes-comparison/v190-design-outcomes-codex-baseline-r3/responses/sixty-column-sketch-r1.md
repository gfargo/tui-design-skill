The repository and commit panes alone require 68 columns, leaving no room for a diff at 60. I’d switch to one full-width pane, initially showing commits.

This sketch is exactly **60 columns × 24 rows**, including borders; repository and commits are illustrative.

```text
+----------------------------------------------------------+
| Git browser | 1 Repos   2 Commits*   3 Diff                |
+----------------------------------------------------------+
| Repository: ~/src/git-browser                            |
| Branch: main                                             |
+----------------------------------------------------------+
|> a1b2c3d  Fix narrow-terminal layout                      |
|  b2c3d4e  Add keyboard navigation                         |
|  c3d4e5f  Highlight selected commit                       |
|  d4e5f6a  Load repository history                         |
|  e5f6a7b  Add diff scrolling                              |
|  f6a7b8c  Initial commit                                  |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
+----------------------------------------------------------+
| j/k Move  Enter Diff  1 Repos  2 Commits  3 Diff           |
| Selected: a1b2c3d | 1/6                                   |
| q Quit                                                   |
+----------------------------------------------------------+
```

- **Reach other panes:** `1`, `2`, and `3` switch to repositories, commits, and diff. `Enter` on a repository opens its commits; `Enter` on a commit opens its diff. `Esc` returns to the previous pane. Selections and scroll positions survive switching.
- **Reach offscreen content:** `j/k` or arrows scroll vertically; Page Up/Down scroll by page. Left/Right scroll long diff lines horizontally.
- **Smaller terminals:** Keep one pane visible and shorten the header and help. Remove blank space and optional metadata as height decreases. The commit pane’s 40-column minimum includes borders: below **40 columns**, show a compact “Terminal too small—resize to at least 40 × 6” message instead of squeezing commits. Below **6 rows**, do the same. Clip that message if necessary; preserve state and restore the view automatically when space returns.