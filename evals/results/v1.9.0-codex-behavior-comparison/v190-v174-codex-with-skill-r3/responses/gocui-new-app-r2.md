**For a new project, I’d use Bubble Tea + Lipgloss, adding Bubbles components where useful.** A lazygit-style interface doesn’t require gocui.

Lazygit’s choice reflects its history and substantial customization: it now carries its gocui fork inside its own repository. Treat lazygit as an interaction-design reference rather than a dependency recommendation.

| Choice | Best reason to use it | Main tradeoff |
|---|---|---|
| **Bubble Tea + Lipgloss** | Custom panes, contextual keys, explicit state transitions, asynchronous operations | You build pane layout and focus routing |
| **tview** | Ready-made tables, trees, forms, and layout containers | Retained widgets and callbacks shape your architecture |
| **gocui** | You specifically want named rectangular views with writable text buffers and per-view bindings | More application infrastructure to own; older library lineage |

Gocui remains reasonable for an existing codebase or if its **views-as-buffers model** fits how you want to work. “Lazygit uses it” alone isn’t a strong reason.

With Bubble Tea, give the root model ownership of layout, focus, and overlays. Give each pane its own selection and scroll state. Route typing to the focused input; run disk, network, and subprocess work through commands that return messages.

Borrow lazygit’s stable pane positions, numeric pane jumps, contextual actions, and footer help. Plan the narrow layout immediately:

```text
Wide                            60 columns
+------------+----------------+ +---------------------------+
| 1 Items    | Detail         | | 1 Items | 2 Detail         |
|            |                | | Active pane fills screen  |
+------------+                | |                           |
| 3 Activity |                | |                           |
+------------+----------------+ +---------------------------+
| Contextual key hints        | | Contextual key hints      |
+-----------------------------+ +---------------------------+
```

At **80×24**, retain list/detail if both remain readable and hide secondary activity. At **60 columns**, use one active pane with detail as a drill-down; preserve selection when switching. Below a declared minimum, show a truthful “terminal too small” state.

Keep chrome restrained: one border layer, no extra outer frame, no repeated row markers, and one contextual hint strip. The lazygit feel comes chiefly from fast navigation and predictable focus.