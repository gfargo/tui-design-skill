Most tree views in terminal apps settle on the same model: `h`/`l` or the arrow keys handle structure, `j`/`k` move the cursor, and `Enter` opens or activates. Whatever your framework, a tree view should cover the following.

## Core keymap

| Key | On a folder | On a leaf |
|---|---|---|
| `l` / `→` | Expand. If it's already open, move to its first child. | Open or activate |
| `h` / `←` | Collapse. If it's already collapsed, move to the parent. | Move to the parent |
| `Enter` | Toggle open/closed, or run the node's action if it has one | Open or activate |
| `j`/`k`, `↑`/`↓` | Move one visible row, without changing expansion | — |
| `g`/`G`, `Home`/`End` | Jump to top / bottom | — |
| `Ctrl+D`/`Ctrl+U`, `PgDn`/`PgUp` | Half page / full page, with one row of overlap on a full page | — |
| `/` | Filter the tree (see below) | — |
| `Space` | Mark the node for a batch action | — |
| `Esc` | Clear the filter or the marks | — |

Pressing `h` repeatedly should climb the tree one parent at a time, and pressing `l` repeatedly should drill down. Users use this all the time, so it has to work.

**Optional:** a "collapse all to top level" key, plus an expand-all key. Expand-all should be limited, or ask first, on lazy or very large trees. Pick keys that don't clash with your other bindings. For example, `*` is a common key for inverting a multi-select.

## Behaviors that matter more than the keys

- **Track state by node ID, not row index.** Keep expansion state, the selected row and marks by ID across refreshes, sorts and filters. If the selected node disappears, select its nearest surviving sibling, then its parent. Don't jump to the top.
- **Load lazily, with a spinner on that node only.** When a folder is expanding, show `▾ src ⠋` on that row and keep the rest of the tree responsive. If loading fails, show the error on that node (`▸ vendor  ! permission denied`) rather than in a modal.
- **Filter keeps the ancestors.** With a filter active, show every match along with its expanded ancestor chain, so the user can see where each match lives. Highlight the matched substring, show a count (`12/4,381`), use smart-case, and respond in under 100 ms. `Esc` should restore the expansion state from before the filter.
- **Keep the cursor steady when content changes.** When a node above the cursor expands or collapses, or a refresh adds rows, keep the selected row at the same screen position. Keep the cursor at least 3 rows from the viewport edge.
- **Virtualize what you render.** Flatten the visible nodes into a list and draw only the rows in the viewport. A fully expanded `node_modules` can easily reach 100,000 rows.
- **Show the user's position.** Put `42/1,203` in the panel title or footer, and in narrow layouts show the path breadcrumb.

## Rendering

- Indent 2 cells per level. Use `├─` and `└─` connectors, with `|-` and `` `- `` as the ASCII fallback.
- For disclosure arrows use `▸` and `▾`, not `▶` and `▼`. The latter have ambiguous width and misalign columns in CJK locales.
- Show the cursor row in reverse video and nothing else. Marked nodes get a `*` prefix. Don't add a bullet to every row, because a marker on every row tells the user nothing.
- Measure names in terminal cells, not string length, and truncate with `…` instead of wrapping.

```
Wide (100 cols)                                  60-col tmux split
┌ Files ─────────── 42/1,203 ┐┌ Preview ──────   ┌ src/ui ──────────── 42/1,203 ┐
│ ▾ src                      ││ fn render(..)    │ ▾ widgets                    │
│ ├─ ▾ ui                    ││   ...            │ │ ├─ tree.rs                 │
│ │  ├─ ▸ widgets            ││                  │ │ └─*list.rs                 │
│ │  ├─*tree.rs              ││                  │ ▸ theme ⠋                    │
│ │  └─ app.rs               ││                  │ app.rs                       │
│ └─ ▸ vendor  ! denied      ││                  └ h up · l open · / filter ────┘
└────────────────────────────┘└──────────────
```

**At 60 columns:** the preview pane hides and opens on `Enter` or `p`. Deep paths are re-rooted onto the current branch, with a breadcrumb in the title. Past about 8 levels, connectors use up the width, so collapse the indent or switch to drill-down (Miller-column style, as in yazi) instead of letting names shrink to `…`.

## Watch for

- **Conflicts with text entry.** While the filter input has focus, `h`, `j`, `k` and `l` are typed characters. Only the arrow keys and `Esc` should navigate then.
- **Mouse support is extra, not required.** Click to select and click the arrow to toggle are fine, but every action needs a keyboard path.
- **Tests:** unit-test the flatten, expand, filter and reselect logic with synthetic key events. Then take snapshot tests of the rendered frames at 80×24 and 60 columns, including a lazy-loading node and a filter result.

These rules come from the skill's interaction and visual-pattern references. If you tell me your framework (Ratatui, Bubble Tea, Textual, Ink), I can map this onto its tree widget or the usual flattened-list approach.
