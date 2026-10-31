At 60×24, show **one full-width pane**, initially the commit list. Repositories plus commits already require `28 + 40 = 68` columns, before any diff.

This is exactly 24 rows and 60 columns; unbordered rows are padded with spaces. Example repository data:

```text
1 Repos   [2 Commits]   3 Diff                                
repo: tui-browser   branch: main                            
+----------------------------------------------------------+
|> a81f02c Fix narrow terminal layout                       |
|  73bc910 Keep selection on resize                         |
|  6e920ad Add repository filter                            |
|  53c8ef1 Handle empty repositories                        |
|  40d2a77 Preserve diff scroll position                    |
|  39a1bc0 Add unified diff view                            |
|  287fd12 Improve keyboard help                            |
|  17cc8ab Initial import                                   |
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
Up/Down select  Enter diff  Esc repos  / filter              
Tab next pane  1/2/3 jump  ? help  q quit                     
```

The pane is **60 columns including borders**, leaving 58 inside. Brackets identify the active pane; `>` identifies only the selected commit.

- **1 / 2 / 3** switch to repositories, commits, or diff, replacing the visible pane. **Tab / Shift+Tab** cycle in that order.
- **Enter** on a repository opens its commits; Enter on a commit opens its unified diff. **Esc** returns one level, restoring selection and scroll position.
- **Up/Down** and **PgUp/PgDn** reach offscreen rows. In the diff, **Left/Right** scroll long lines horizontally; `[` / `]` jump between hunks. Contextual footer hints change with the pane; `?` shows all controls.
- Long commit subjects truncate with `...`; the commit detail shown above its diff contains the full message.

Use these explicit resize rules. The diff minimum of 40 columns is a proposed design choice:

| Terminal width | Layout |
|---|---|
| 108+ | Repositories 28, commits 40, diff remainder; at 140 the diff gets 72 |
| 80–107 | Repository picker hidden; commits 40, diff remainder |
| 40–79 | One pane, full width; other panes remain keyboard-accessible |
| Below 40 | Too-small state |

Declare **40×8** the supported minimum: 40 preserves the commit list’s required width; eight rows allow compact navigation, context, borders, two data rows, and two hint rows. Below 60, shorten hints and omit optional metadata before truncating subjects. Below eight rows or 40 columns, replace the browser with:

```text
Terminal too small
Need 40x8; have 39x7
Resize or q to quit
```

Clip that message to the available cells in extremely small terminals. Keep quit working, preserve browsing state, and restore the layout automatically when space returns. Resizing while viewing a diff keeps that diff active.

The sketch has border depth one, one active-tab cue, and one selected-row marker. Borders and the four navigation/context rows reserve 396 of 1,440 cells (27.5%); omit nested boxes, per-row icons, and repeated repository or branch fields.