Here's a solid baseline, drawn from conventions users already know (file managers, IDE sidebars, ranger/nnn, lazygit, VS Code, Windows/macOS tree controls).

## Core navigation

| Key | Behavior |
|---|---|
| `↑` / `k` | Move to the previous visible node |
| `↓` / `j` | Move to the next visible node |
| `→` / `l` | On a collapsed parent: expand. On an expanded parent: go to its first child. On a leaf: do nothing, or open it if your app works like a file browser. |
| `←` / `h` | On an expanded parent: collapse. Otherwise go to the parent node. **This is the most important behavior to get right.** |
| `Enter` | Activate/open the node. On a parent, toggle expansion if "open" means nothing for it. |
| `Space` | Toggle expand/collapse, or toggle selection if you support multi-select. Pick one and stay consistent. |
| `Home` / `g` | Jump to the first node |
| `End` / `G` | Jump to the last visible node |
| `PgUp` / `PgDn` (`Ctrl-u` / `Ctrl-d`) | Move by a page or half page |

## Bulk expand/collapse

| Key | Behavior |
|---|---|
| `*` or `E` | Expand all descendants of the current node |
| `-` or `C` | Collapse all (whole tree, or the current subtree) |
| `zo` / `zc` / `zR` / `zM` | Optional vim-fold style, for vim-heavy audiences |
| `p` or `Backspace` | Jump to the parent without collapsing |

## Search and filter

- `/` starts an incremental search, and `n` / `N` go to the next/previous match. Matches inside collapsed nodes should **auto-expand their ancestors** so the match is visible.
- Type-ahead (typing letters jumps to the next sibling starting with them) is nice, but it conflicts with single-letter commands. Choose one.
- Filter mode is optional: it hides non-matching nodes but keeps the ancestors of matches.

## Selection (if you need it)

- `Space` or `v` toggles a mark on the current node.
- `Shift+↑/↓` extends a range.
- Decide what marking a parent means (does it select its children?) and show a partial state (`◐` or `[-]`) for mixed children.

## Behaviors that matter as much as the keys

1. **Keep the cursor stable.** When you collapse a node, the cursor stays on it. When the tree refreshes or reloads, restore the cursor by node identity, not by row index.
2. **Remember expansion state** per node across refreshes, and ideally across sessions.
3. **Scroll with a margin.** Keep a few rows of context above and below the cursor (vim's `scrolloff`), and center the cursor on big jumps.
4. **Load lazily.** Show a `…` or spinner for children that are still loading, and don't block input while you fetch.
5. **Use clear indicators.** `▸`/`▾` (or `+`/`-` as an ASCII fallback) for collapsed/expanded, and no indicator on leaves. Indent guides (`│ ├ └`) help with deep trees.
6. **Handle long labels.** Truncate with `…` instead of wrapping, and show the full text in a status line for the focused node.
7. **Show where you are.** A breadcrumb or path of the focused node in a header or footer helps a lot in deep trees.
8. **Handle empty states.** "No items" or "(empty)" under an expanded parent with no children, so it doesn't look broken.
9. **Support the mouse if your framework allows it.** Click selects, clicking the arrow toggles, double-click activates, and the scroll wheel scrolls.
10. **Make it discoverable.** Put a `?` help overlay or a one-line key hint in the footer.

## Common mistakes to avoid

- Making `←` on a leaf do nothing. Users expect it to jump to the parent.
- Resetting scroll position or expansion on every data update.
- Having `Enter` do different things on parents and leaves with no visual hint.
- Relying only on color to show state. Use glyphs too, for monochrome terminals and colorblind users.

If you tell me which framework you're using (Bubble Tea, Textual, Ratatui, Ink, etc.) and what the tree holds (files, JSON, a git tree, etc.), I can map these to that framework's conventions and point out which ones it already gives you.
