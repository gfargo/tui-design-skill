For a terminal list view, use familiar keys and keep the selected item visible:

| Key | Action |
|---|---|
| `↑` / `↓` | Move selection one item |
| `j` / `k` | Optional aliases for down / up |
| `Page Up` / `Page Down` | Move roughly one visible page, keeping one row of overlap |
| `Home` / `End` | Select the first / last item |
| `g` / `G` | Optional aliases for first / last, unless typing searches the list |
| Mouse wheel | Scroll through the list |

Avoid wrapping from the last item to the first by default; it makes position harder to track.

Use a compact **`24 / 180`** indicator for the selected item’s position. If rows can scroll independently of selection, show the visible range instead: **`21–40 of 180`**. A thin scrollbar can add a useful visual cue for long lists, but a percentage alone is less informative.

For an empty list, show **“No items”** rather than `0 / 0`. If the total is unknown, show **“24 loaded”** or **“Loading more…”** instead of implying a known endpoint.